import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_notifications_flow(client: AsyncClient):
    # Fetch notifications
    list_resp = await client.get("/api/notifications")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)

    # Read-all endpoint
    read_all_resp = await client.post("/api/notifications/read-all")
    assert read_all_resp.status_code == 200
    assert read_all_resp.json()["message"] == "All notifications marked as read"
