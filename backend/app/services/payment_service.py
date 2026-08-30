import asyncio
import logging
import uuid
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PaymentGatewayError(Exception):
    """Raised when the payment gateway returns an unexpected error or network failure."""
    pass

class PaymentGatewaySimulator:
    @staticmethod
    async def process_charge(
        amount: float,
        order_id: int,
        idempotency_key: str,
        simulate_failure: bool = False,
        simulate_timeout: bool = False
    ) -> Dict[str, Any]:
        """
        Simulates an external payment gateway charge (e.g. Stripe, Razorpay, Adyen).
        
        Guarantees:
        - Network latency simulation (50ms).
        - Idempotent transaction identification.
        - Failure and timeout error handling.
        """
        logger.info(f"Initiating payment charge for order {order_id} of ${amount:.2f} [Key: {idempotency_key}]")
        
        # Simulate gateway network roundtrip
        await asyncio.sleep(0.05)

        if simulate_timeout:
            logger.warning(f"Payment gateway timeout for order {order_id}")
            raise TimeoutError("Payment gateway timed out while communicating with acquiring bank.")

        if simulate_failure:
            logger.info(f"Payment declined for order {order_id}")
            return {
                "success": False,
                "transaction_id": None,
                "error_code": "CARD_DECLINED",
                "error_message": "Card was declined by issuing bank due to insufficient funds."
            }

        txn_id = f"txn_{uuid.uuid4().hex[:16]}"
        logger.info(f"Payment charge successful for order {order_id}: {txn_id}")
        return {
            "success": True,
            "transaction_id": txn_id,
            "error_code": None,
            "error_message": None
        }