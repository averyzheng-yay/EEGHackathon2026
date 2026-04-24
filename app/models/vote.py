import uuid
import enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TargetType(enum.Enum):
    paper = "paper"
    post = "post"


class VoteType(enum.Enum):
    up = "up"
    down = "down"


class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Exactly one of user_id / session_id must be set.
    # user_id is set for authenticated votes; session_id for anonymous.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)

    target_type = Column(SAEnum(TargetType), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vote_type = Column(SAEnum(VoteType), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="votes")
