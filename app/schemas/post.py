from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import CursorPage


class PostAuthor(BaseModel):
    id: UUID
    username: str

    model_config = {"from_attributes": True}


class LinkedPaperSnippet(BaseModel):
    id: UUID
    arxiv_id: str
    title: str

    model_config = {"from_attributes": True}


class PostCard(BaseModel):
    """Compact card for the home feed."""
    id: UUID
    title: str
    author: PostAuthor | None
    tags: list[str]
    technical_level: str
    upvote_count: int
    downvote_count: int
    comment_count: int
    created_at: datetime
    linked_paper: LinkedPaperSnippet | None = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "a2b3c4d5-e6f7-8901-abcd-ef1234567890",
                "title": "Chain-of-thought prompting is just vibes, right? Let's discuss",
                "author": {"id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "username": "riya_reads"},
                "tags": ["artificial-intelligence", "natural-language-processing"],
                "technical_level": "intermediate",
                "upvote_count": 67,
                "downvote_count": 3,
                "comment_count": 23,
                "created_at": "2024-04-17T14:22:00Z",
                "linked_paper": {
                    "id": "1c8b2f4d-e5a3-4b6c-9d1e-2f3a4b5c6d7e",
                    "arxiv_id": "2404.12345",
                    "title": "Emergent Reasoning in Large Language Models via Chain-of-Thought Scaffolding",
                },
            }
        },
    }


class PostDetail(PostCard):
    """Full post detail including body text."""
    body: str
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "a2b3c4d5-e6f7-8901-abcd-ef1234567890",
                "title": "Chain-of-thought prompting is just vibes, right? Let's discuss",
                "body": "I've been reading the Chen et al. paper linked here and I keep coming back to the question: are we just pattern-matching on reasoning *style* rather than actual logical capability? The GSM8K results are impressive but...",
                "author": {"id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "username": "riya_reads"},
                "tags": ["artificial-intelligence", "natural-language-processing"],
                "technical_level": "intermediate",
                "upvote_count": 67,
                "downvote_count": 3,
                "comment_count": 23,
                "created_at": "2024-04-17T14:22:00Z",
                "updated_at": "2024-04-17T14:22:00Z",
                "linked_paper": {
                    "id": "1c8b2f4d-e5a3-4b6c-9d1e-2f3a4b5c6d7e",
                    "arxiv_id": "2404.12345",
                    "title": "Emergent Reasoning in Large Language Models via Chain-of-Thought Scaffolding",
                },
            }
        },
    }


class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    body: str = Field(..., min_length=10)
    technical_level: str = Field("intermediate", pattern="^(beginner|intermediate|expert)$")
    tags: list[str] = Field(default_factory=list, max_length=8)
    paper_id: UUID | None = Field(None, description="Optional UUID of a paper in the database to link")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Chain-of-thought prompting is just vibes, right? Let's discuss",
                "body": "I've been reading the Chen et al. paper and I keep coming back to a nagging question...",
                "technical_level": "intermediate",
                "tags": ["artificial-intelligence", "natural-language-processing"],
                "paper_id": "1c8b2f4d-e5a3-4b6c-9d1e-2f3a4b5c6d7e",
            }
        }
    }


class UpdatePostRequest(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=500)
    body: str | None = Field(None, min_length=10)
    technical_level: str | None = Field(None, pattern="^(beginner|intermediate|expert)$")
    tags: list[str] | None = Field(None, max_length=8)


PostFeed = CursorPage[PostCard]
