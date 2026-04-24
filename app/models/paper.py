import uuid

from sqlalchemy import Column, String, Text, Integer, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arxiv_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    authors = Column(ARRAY(String), nullable=False, default=list)
    year = Column(Integer, nullable=True)
    abstract = Column(Text, nullable=True)

    # Both summaries are generated once at ingest time by Qwen; null until then.
    plain_summary = Column(Text, nullable=True)
    technical_summary = Column(Text, nullable=True)

    tags = Column(ARRAY(String), nullable=False, default=list)
    primary_category = Column(String(50), nullable=True)

    upvote_count = Column(Integer, default=0, nullable=False)
    downvote_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)

    published_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    arxiv_url = Column(String(255), nullable=True)

    posts = relationship("Post", back_populates="paper")
    votes = relationship("Vote", primaryjoin="and_(Vote.target_id == Paper.id, Vote.target_type == 'paper')", foreign_keys="Vote.target_id", overlaps="votes")
    recommendation_scores = relationship("RecommendationScore", back_populates="paper", cascade="all, delete-orphan")
