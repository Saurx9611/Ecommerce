from sqlalchemy import Column, Integer, String, Text, BigInteger, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(String(255), nullable=False)
    audio_url = Column(String(512), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    mime_type = Column(String(64), nullable=False)
    duration = Column(Float, nullable=True, default=0.0)  # In seconds
    language = Column(String(16), nullable=True, default="en")
    
    # Statuses: uploaded, queued, transcribing, speaker_detection, chunking, embedding, indexing, completed, failed
    status = Column(String(32), nullable=False, default="uploaded", index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="episodes")
    speakers = relationship("Speaker", back_populates="episode", cascade="all, delete-orphan", lazy="selectin", order_by="Speaker.id")
    transcript_segments = relationship("TranscriptSegment", back_populates="episode", cascade="all, delete-orphan", order_by="TranscriptSegment.sequence_number")
    embeddings = relationship("ChunkEmbedding", back_populates="episode", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="episode", cascade="all, delete-orphan", order_by="desc(ProcessingJob.started_at)")
    insights = relationship("EpisodeInsight", back_populates="episode", cascade="all, delete-orphan", uselist=False)
