from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Speaker(Base):
    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(64), nullable=False)            # e.g., "Speaker 1", "Speaker 2"
    display_name = Column(String(128), nullable=False)     # e.g., "Lex Fridman", "Sam Altman"
    speaking_duration = Column(Float, nullable=False, default=0.0)
    segment_count = Column(Integer, nullable=False, default=0)

    episode = relationship("Episode", back_populates="speakers")
    segments = relationship("TranscriptSegment", back_populates="speaker")
