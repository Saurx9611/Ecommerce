from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NotificationRead(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
