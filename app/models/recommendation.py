from sqlalchemy import Column, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RecommendationScore(Base):
    __tablename__ = "recommendation_scores"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True)
    score = Column(Float, nullable=False, default=0.0)
    computed_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="recommendation_scores")
    paper = relationship("Paper", back_populates="recommendation_scores")
