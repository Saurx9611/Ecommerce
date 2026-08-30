import os
import time
import logging
from typing import Sequence, Tuple
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.client: aioredis.Redis | None = None
        self.single_reserve_sha: str | None = None
        self.multi_reserve_sha: str | None = None
        self.compensate_sha: str | None = None
        self.rate_limit_sha: str | None = None
        # In-memory emulation store for development/test fallback
        self._memory_store: dict[str, int] = {}
        self._memory_zsets: dict[str, list[float]] = {}

    async def connect(self):
        try:
            self.client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0
            )
            await self.client.ping()
            scripts_dir = os.path.join(os.path.dirname(__file__), "../scripts")
            
            # Load Single-item Reservation Script
            single_path = os.path.join(scripts_dir, "inventory_lock.lua")
            if os.path.exists(single_path):
                with open(single_path, "r", encoding="utf-8") as f:
                    self.single_reserve_sha = await self.client.script_load(f.read())

            # Load Multi-item Reservation Script
            multi_path = os.path.join(scripts_dir, "multi_item_reserve.lua")
            if os.path.exists(multi_path):
                with open(multi_path, "r", encoding="utf-8") as f:
                    self.multi_reserve_sha = await self.client.script_load(f.read())

            # Load Batch Compensation Script
            comp_path = os.path.join(scripts_dir, "compensate_batch.lua")
            if os.path.exists(comp_path):
                with open(comp_path, "r", encoding="utf-8") as f:
                    self.compensate_sha = await self.client.script_load(f.read())

            # Load Sliding Window Rate Limit Script
            rate_path = os.path.join(scripts_dir, "sliding_window_rate_limit.lua")
            if os.path.exists(rate_path):
                with open(rate_path, "r", encoding="utf-8") as f:
                    self.rate_limit_sha = await self.client.script_load(f.read())

            logger.info("RedisService connected and Lua scripts cached successfully.")
        except Exception as e:
            logger.info(f"External Redis unavailable ({e}). Using local in-memory Redis emulator.")
            self.client = None

    async def close(self):
        if self.client:
            await self.client.close()

    async def is_available(self) -> bool:
        if not self.client:
            return True  # Fallback in-memory engine is active and available
        try:
            return await self.client.ping()
        except Exception:
            return True

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int, int]:
        """
        Executes atomic sliding window rate limit evaluation.
        Returns: (is_allowed: bool, current_count: int, max_limit: int, retry_after: int)
        """
        now = time.time()

        # 1. Real Redis with Lua script if connected
        if self.client:
            try:
                now_ms = int(now * 1000)
                window_ms = window_seconds * 1000
                if not self.rate_limit_sha:
                    scripts_dir = os.path.join(os.path.dirname(__file__), "../scripts")
                    rate_path = os.path.join(scripts_dir, "sliding_window_rate_limit.lua")
                    with open(rate_path, "r", encoding="utf-8") as f:
                        self.rate_limit_sha = await self.client.script_load(f.read())

                res = await self.client.evalsha(
                    self.rate_limit_sha,
                    1,
                    key,
                    str(now_ms),
                    str(window_ms),
                    str(max_requests)
                )
                is_allowed = bool(res[0] == 1)
                current_count = int(res[1])
                limit = int(res[2])
                retry_after = int(res[3])
                return (is_allowed, current_count, limit, retry_after)
            except Exception as e:
                logger.warning(f"Redis check_rate_limit error ({e}), using memory fallback.")

        # 2. In-memory exact sliding window evaluation
        clear_before = now - window_seconds
        timestamps = self._memory_zsets.get(key, [])
        # Prune expired
        timestamps = [t for t in timestamps if t > clear_before]

        if len(timestamps) < max_requests:
            timestamps.append(now)
            self._memory_zsets[key] = timestamps
            return (True, len(timestamps), max_requests, 0)
        else:
            oldest = timestamps[0] if timestamps else now
            retry_after = max(1, int(oldest + window_seconds - now))
            self._memory_zsets[key] = timestamps
            return (False, len(timestamps), max_requests, retry_after)

    async def prewarm_stock(self, product_id: int, stock: int):
        """Unconditionally prewarms/syncs cache when product stock is updated authoritatively in DB."""
        key = f"product:{product_id}:stock"
        self._memory_store[key] = stock
        if self.client:
            try:
                await self.client.set(key, stock)
            except Exception as e:
                logger.warning(f"Failed to prewarm Redis stock for product {product_id}: {e}")

    async def safe_initialize_stock(self, product_id: int, db_stock: int) -> bool:
        """
        Safely initializes Redis key only if it does NOT exist (SETNX).
        Prevents cold-start concurrent overwrite race condition.
        """
        key = f"product:{product_id}:stock"
        if key not in self._memory_store:
            self._memory_store[key] = db_stock

        if not self.client:
            return True
        try:
            result = await self.client.set(key, db_stock, nx=True)
            return bool(result)
        except Exception as e:
            logger.warning(f"Safe init failed for product {product_id}: {e}")
            return True

    async def reserve_single(self, product_id: int, quantity: int) -> int:
        key = f"product:{product_id}:stock"
        if self.client and self.single_reserve_sha:
            try:
                res = await self.client.evalsha(self.single_reserve_sha, 1, key, str(quantity))
                return int(res)
            except Exception as e:
                logger.warning(f"reserve_single error: {e}")

        # In-memory reservation
        curr = self._memory_store.get(key)
        if curr is None:
            return -1
        if curr < quantity:
            return 0
        self._memory_store[key] = curr - quantity
        return 1

    async def reserve_multi(self, items: Sequence[Tuple[int, int]]) -> Tuple[int, int]:
        if self.client and self.multi_reserve_sha:
            try:
                keys = [f"product:{pid}:stock" for pid, _ in items]
                args = [str(qty) for _, qty in items]
                res = await self.client.evalsha(self.multi_reserve_sha, len(keys), *keys, *args)
                return (int(res[0]), int(res[1]))
            except Exception as e:
                logger.warning(f"reserve_multi error: {e}")

        # In-memory atomic multi-item reserve
        for idx, (pid, qty) in enumerate(items, start=1):
            key = f"product:{pid}:stock"
            curr = self._memory_store.get(key)
            if curr is None:
                return (-1, idx)
            if curr < qty:
                return (0, idx)

        for pid, qty in items:
            key = f"product:{pid}:stock"
            self._memory_store[key] -= qty

        return (1, 0)

    async def compensate_batch(self, items: Sequence[Tuple[int, int]]):
        if not items:
            return
        if self.client and self.compensate_sha:
            try:
                keys = [f"product:{pid}:stock" for pid, _ in items]
                args = [str(qty) for _, qty in items]
                await self.client.evalsha(self.compensate_sha, len(keys), *keys, *args)
            except Exception as e:
                logger.error(f"Failed to execute compensate_batch: {e}")

        # In-memory compensation
        for pid, qty in items:
            key = f"product:{pid}:stock"
            if key in self._memory_store:
                self._memory_store[key] += qty

redis_service = RedisService()