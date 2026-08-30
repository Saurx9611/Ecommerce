from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="queued") # queued, processing, completed, failed
    current_stage = Column(String(64), nullable=False, default="upload") # upload, transcription, speaker_detection, chunking, embedding, indexing, complete
    progress = Column(Float, nullable=False, default=0.0) # 0.0 - 100.0
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    episode = relationship("Episode", back_populates="processing_jobs")
