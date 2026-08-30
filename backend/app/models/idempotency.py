from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_keys"

    idempotency_key = Column(String(128), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    status_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    locked_until = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED')", name="chk_idempotency_status_valid"),
    )