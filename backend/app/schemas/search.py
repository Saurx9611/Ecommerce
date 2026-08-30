from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SearchRequest(BaseModel):
    query: str
    project_id: int | None = None
    episode_id: int | None = None
    limit: int = 15
    min_score: float = 0.0

class SavedSearchCreate(BaseModel):
    name: str
    query: str
    project_id: int | None = None
    filters: dict | None = None

class SavedSearchUpdate(BaseModel):
    name: str | None = None
    query: str | None = None
    filters: dict | None = None

class SavedSearchRead(BaseModel):
    id: int
    user_id: int
    project_id: int | None = None
    name: str
    query: str
    filters: dict | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
