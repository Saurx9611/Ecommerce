import asyncio
import httpx
import uuid

BASE_URL = "http://localhost:8000"

async def attempt_purchase(client: httpx.AsyncClient, user_idx: int, product_id: int):
    headers = {"Idempotency-Key": str(uuid.uuid4())}
    payload = {
        "user_id": f"user_{user_idx}",
        "items": [{"product_id": product_id, "quantity": 1}]
    }
    try:
        resp = await client.post(f"{BASE_URL}/orders/flash-checkout", json=payload, headers=headers)
        return resp.status_code
    except Exception as e:
        return f"Error: {e}"

async def main():
    async with httpx.AsyncClient() as client:
        # Create product with stock = 10
        prod_resp = await client.post(f"{BASE_URL}/products/", json={
            "title": "Limited Edition GPU",
            "price": 499.99,
            "stock": 10
        })
        product_id = prod_resp.json()["id"]
        print(f"Created Product {product_id} with stock = 10")

        # Launch 100 concurrent purchase attempts
        tasks = [attempt_purchase(client, i, product_id) for i in range(100)]
        results = await asyncio.gather(*tasks)

        success_count = results.count(201)
        sold_out_count = results.count(410)
        print(f"\n--- Concurrency Results ---")
        print(f"Total Requests : {len(results)}")
        print(f"201 Created    : {success_count} (Must be exactly 10)")
        print(f"410 Sold Out   : {sold_out_count} (Must be exactly 90)")

if __name__ == "__main__":
    asyncio.run(main())