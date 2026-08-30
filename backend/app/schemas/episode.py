from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SpeakerBase(BaseModel):
    label: str
    display_name: str
    speaking_duration: float = 0.0
    segment_count: int = 0

class SpeakerUpdate(BaseModel):
    display_name: str

class SpeakerRead(SpeakerBase):
    id: int
    episode_id: int
    model_config = ConfigDict(from_attributes=True)

class TranscriptSegmentRead(BaseModel):
    id: int
    episode_id: int
    speaker_id: int | None = None
    speaker: SpeakerRead | None = None
    text: str
    start_time: float
    end_time: float
    sequence_number: int
    confidence: float
    model_config = ConfigDict(from_attributes=True)

class EpisodeInsightRead(BaseModel):
    id: int
    episode_id: int
    overview: str
    target_competencies: list[dict]
    core_tech_stack: list[dict]
    architectural_blueprint: dict
    resume_transformation: list[dict]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProcessingJobRead(BaseModel):
    id: int
    episode_id: int
    status: str
    current_stage: str
    progress: float
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class EpisodeBase(BaseModel):
    title: str
    description: str | None = None
    language: str | None = "en"

class EpisodeCreate(EpisodeBase):
    project_id: int

class EpisodeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

class EpisodeRead(EpisodeBase):
    id: int
    project_id: int
    original_filename: str
    audio_url: str
    file_size: int
    mime_type: str
    duration: float | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None
    speakers: list[SpeakerRead] = []
    model_config = ConfigDict(from_attributes=True)
