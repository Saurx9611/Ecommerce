from sqlalchemy import Column, Integer, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    speaker_id = Column(Integer, ForeignKey("speakers.id", ondelete="SET NULL"), nullable=True, index=True)
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False, index=True)   # In seconds (e.g. 112.4)
    end_time = Column(Float, nullable=False)                 # In seconds (e.g. 138.8)
    sequence_number = Column(Integer, nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=1.0)

    episode = relationship("Episode", back_populates="transcript_segments")
    speaker = relationship("Speaker", back_populates="segments")
    embeddings = relationship("ChunkEmbedding", back_populates="segment")

    __table_args__ = (
        Index("idx_segment_episode_seq", "episode_id", "sequence_number"),
    )
