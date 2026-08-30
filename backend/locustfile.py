import uuid
from locust import HttpUser, task, between, tag

class BrowsingUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @tag('browse')
    @task(3)
    def browse_products(self):
        self.client.get("/api/products/", name="/api/products/")

    @tag('browse')
    @task(2)
    def browse_categories(self):
        self.client.get("/api/products/categories/summary", name="/api/products/categories/summary")

    @tag('browse')
    @task(1)
    def check_health(self):
        self.client.get("/healthz", name="/healthz")

class FlashSaleUser(HttpUser):
    wait_time = between(0.01, 0.1)

    @tag('flash_sale')
    @task
    def buy_flash_item(self):
        idempotency_key = f"locust-key-{uuid.uuid4()}"
        headers = {
            "Idempotency-Key": idempotency_key,
            "X-Forwarded-For": f"10.0.{uuid.uuid4().int % 200}.{uuid.uuid4().int % 250 + 1}"
        }
        payload = {
            "items": [{"product_id": 1, "quantity": 1}]
        }
        with self.client.post(
            "/api/orders/flash-checkout",
            json=payload,
            headers=headers,
            catch_response=True,
            name="/api/orders/flash-checkout"
        ) as response:
            if response.status_code in [201, 409, 410, 429]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
