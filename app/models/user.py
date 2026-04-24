import uuid
import enum

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Enum as SAEnum, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ExpertiseLevel(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    expert = "expert"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    expertise_level = Column(SAEnum(ExpertiseLevel), default=ExpertiseLevel.beginner, nullable=False)
    onboarding_complete = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

    interests = relationship("UserInterest", back_populates="user", cascade="all, delete-orphan", order_by="UserInterest.priority")
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    votes = relationship("Vote", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    recommendation_scores = relationship("RecommendationScore", back_populates="user", cascade="all, delete-orphan")


class UserInterest(Base):
    __tablename__ = "user_interests"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tag_slug = Column(String(100), primary_key=True)
    # 1 = highest priority; used to seed recommendations
    priority = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="interests")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False)  # sha256 hex digest
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
