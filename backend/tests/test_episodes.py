import io
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_project_and_episode_flow(client: AsyncClient):
    # 1. Create Project
    proj_resp = await client.post("/api/projects", json={
        "name": "Engineering Deep Dives",
        "description": "High performance software engineering podcasts"
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]
    assert project_id is not None

    # 2. Upload Episode
    fake_audio = io.BytesIO(b"FAKE_AUDIO_BYTES_TEST_STREAM")
    files = {"file": ("test_episode.mp3", fake_audio, "audio/mpeg")}
    data = {
        "project_id": project_id,
        "title": "Scaling Distributed Architectures",
        "description": "Episode discussing pgvector and temporal chunking.",
        "language": "en"
    }
    ep_resp = await client.post("/api/episodes", data=data, files=files)
    assert ep_resp.status_code == 201
    episode_data = ep_resp.json()
    episode_id = episode_data["id"]
    assert episode_data["title"] == "Scaling Distributed Architectures"

    # 3. List Episodes
    list_resp = await client.get(f"/api/episodes?project_id={project_id}")
    assert list_resp.status_code == 200
    episodes = list_resp.json()
    assert len(episodes) >= 1
    assert episodes[0]["id"] == episode_id

    # 4. Get Episode Detail
    detail_resp = await client.get(f"/api/episodes/{episode_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == episode_id
