from sqlalchemy import Column, Integer, Text, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class EpisodeInsight(Base):
    __tablename__ = "episode_insights"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    overview = Column(Text, nullable=False)
    target_competencies = Column(JSON, nullable=False, default=list)
    core_tech_stack = Column(JSON, nullable=False, default=list)
    architectural_blueprint = Column(JSON, nullable=False, default=dict)
    resume_transformation = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    episode = relationship("Episode", back_populates="insights")
