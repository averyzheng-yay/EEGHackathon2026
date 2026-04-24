from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import CursorPage


class PaperCard(BaseModel):
    """Compact representation used in the Reels feed and search results."""
    id: UUID
    arxiv_id: str
    title: str
    authors: list[str]
    year: int | None
    tags: list[str]
    primary_category: str | None
    plain_summary: str | None
    technical_summary: str | None
    upvote_count: int
    downvote_count: int
    view_count: int
    published_at: datetime | None
    arxiv_url: str | None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "1c8b2f4d-e5a3-4b6c-9d1e-2f3a4b5c6d7e",
                "arxiv_id": "2404.12345",
                "title": "Emergent Reasoning in Large Language Models via Chain-of-Thought Scaffolding",
                "authors": ["Alex Chen", "Priya Nair", "Johann Müller"],
                "year": 2024,
                "tags": ["artificial-intelligence", "natural-language-processing", "deep-learning"],
                "primary_category": "cs.AI",
                "plain_summary": "This paper shows that LLMs get dramatically better at hard math and logic problems when you ask them to 'think out loud' step by step, instead of jumping straight to an answer...",
                "technical_summary": None,
                "upvote_count": 142,
                "downvote_count": 8,
                "view_count": 1840,
                "published_at": "2024-04-15T00:00:00Z",
                "arxiv_url": "https://arxiv.org/abs/2404.12345",
            }
        },
    }


class PaperDetail(PaperCard):
    """Full paper detail page — includes abstract and linked discussion posts."""
    abstract: str | None
    ingested_at: datetime
    linked_posts: list[dict] = Field(default_factory=list, description="Discussion posts linked to this paper")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "1c8b2f4d-e5a3-4b6c-9d1e-2f3a4b5c6d7e",
                "arxiv_id": "2404.12345",
                "title": "Emergent Reasoning in Large Language Models via Chain-of-Thought Scaffolding",
                "authors": ["Alex Chen", "Priya Nair", "Johann Müller"],
                "year": 2024,
                "abstract": "We investigate the effect of chain-of-thought prompting on multi-step reasoning tasks across a suite of frontier language models...",
                "plain_summary": "This paper shows that LLMs get dramatically better at hard math and logic problems when you ask them to 'think out loud'...",
                "technical_summary": "We conduct ablation studies on CoT prompting across GPT-4, Gemini Ultra, and Claude 3 Opus on BIG-Bench Hard, GSM8K, and MATH...",
                "tags": ["artificial-intelligence", "natural-language-processing", "deep-learning"],
                "primary_category": "cs.AI",
                "upvote_count": 142,
                "downvote_count": 8,
                "view_count": 1840,
                "published_at": "2024-04-15T00:00:00Z",
                "ingested_at": "2024-04-16T02:14:33Z",
                "arxiv_url": "https://arxiv.org/abs/2404.12345",
                "linked_posts": [
                    {
                        "id": "post-uuid-1",
                        "title": "Chain-of-thought prompting is just vibes, right? Let's discuss",
                        "author_username": "riya_reads",
                        "comment_count": 23,
                        "upvote_count": 67,
                    }
                ],
            }
        },
    }


class VoteRequest(BaseModel):
    vote_type: str = Field(..., pattern="^(up|down)$")
    # Anonymous votes include a session_id from the frontend
    session_id: str | None = None


class VoteResponse(BaseModel):
    upvote_count: int
    downvote_count: int
    user_vote: str | None = None  # "up", "down", or null


PaperFeed = CursorPage[PaperCard]
