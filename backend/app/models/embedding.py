from sqlalchemy import Column, Integer, Text, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.config import settings

class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("transcript_segments.id", ondelete="SET NULL"), nullable=True)
    speaker_label = Column(Text, nullable=True)
    chunk_text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False, index=True)
    end_time = Column(Float, nullable=False)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    episode = relationship("Episode", back_populates="embeddings")
    segment = relationship("TranscriptSegment", back_populates="embeddings")
