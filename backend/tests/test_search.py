import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_saved_search_crud_and_duplicate(client: AsyncClient):
    # 1. Create Saved Search
    create_resp = await client.post("/api/search/saved", json={
        "name": "pgvector discussions",
        "query": "How does vector indexing work with pgvector?",
        "filters": {"min_score": 0.5}
    })
    assert create_resp.status_code == 201
    saved_data = create_resp.json()
    saved_id = saved_data["id"]
    assert saved_data["name"] == "pgvector discussions"

    # 2. List Saved Searches
    list_resp = await client.get("/api/search/saved")
    assert list_resp.status_code == 200
    searches = list_resp.json()
    assert any(s["id"] == saved_id for s in searches)

    # 3. Duplicate Saved Search
    dup_resp = await client.post(f"/api/search/saved/{saved_id}/duplicate")
    assert dup_resp.status_code == 201
    dup_data = dup_resp.json()
    assert dup_data["name"] == "pgvector discussions (Copy)"
    assert dup_data["query"] == saved_data["query"]

    # 4. Delete Original
    del_resp = await client.delete(f"/api/search/saved/{saved_id}")
    assert del_resp.status_code == 204
