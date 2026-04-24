from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserInterestItem(BaseModel):
    tag_slug: str
    priority: int

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """Public-facing user profile — no PII."""
    id: UUID
    username: str
    expertise_level: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "username": "riya_reads",
                "expertise_level": "intermediate",
                "created_at": "2025-04-01T10:00:00Z",
            }
        },
    }


class UserMe(BaseModel):
    """Full user profile returned to the authenticated user."""
    id: UUID
    email: str
    username: str
    expertise_level: str
    onboarding_complete: bool
    interests: list[UserInterestItem]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "email": "riya@example.com",
                "username": "riya_reads",
                "expertise_level": "intermediate",
                "onboarding_complete": True,
                "interests": [
                    {"tag_slug": "artificial-intelligence", "priority": 1},
                    {"tag_slug": "machine-learning", "priority": 2},
                ],
                "created_at": "2025-04-01T10:00:00Z",
                "updated_at": "2025-04-10T08:30:00Z",
            }
        },
    }


class OnboardingRequest(BaseModel):
    """Sent after signup to capture expertise level and top 5 interest tags."""
    expertise_level: str = Field(..., pattern="^(beginner|intermediate|expert)$")
    interests: list[str] = Field(..., min_length=1, max_length=10, description="Tag slugs from the taxonomy")

    model_config = {
        "json_schema_extra": {
            "example": {
                "expertise_level": "intermediate",
                "interests": [
                    "artificial-intelligence",
                    "machine-learning",
                    "natural-language-processing",
                    "cognitive-science",
                    "neuroscience",
                ],
            }
        }
    }


class UpdateUserRequest(BaseModel):
    expertise_level: str | None = Field(None, pattern="^(beginner|intermediate|expert)$")
    interests: list[str] | None = Field(None, max_length=10)

    model_config = {
        "json_schema_extra": {
            "example": {"expertise_level": "expert", "interests": ["artificial-intelligence", "deep-learning"]}
        }
    }


class AuthResponse(BaseModel):
    """Returned on register and login — tokens + user in one payload."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserMe

    model_config = {"from_attributes": True}
