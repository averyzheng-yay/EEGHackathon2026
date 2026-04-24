import uuid
import enum

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SAEnum, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class TechnicalLevel(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    expert = "expert"


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)

    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # Optional link to a paper in the database
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True, index=True)

    technical_level = Column(SAEnum(TechnicalLevel), default=TechnicalLevel.intermediate, nullable=False)
    tags = Column(ARRAY(String), nullable=False, default=list)

    upvote_count = Column(Integer, default=0, nullable=False)
    downvote_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

    author = relationship("User", back_populates="posts")
    paper = relationship("Paper", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
