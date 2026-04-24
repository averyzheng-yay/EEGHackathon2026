from pydantic import BaseModel

from app.schemas.paper import PaperCard
from app.schemas.post import PostCard


class SearchResponse(BaseModel):
    """
    Unified search result.  The frontend renders these in two tabs:
    'Papers' and 'Discussions'.  Both lists are returned in one request
    so the tab counts are accurate without a second round-trip.
    """
    query: str
    tag_filter: str | None
    papers: list[PaperCard]
    posts: list[PostCard]
    total_papers: int
    total_posts: int
    # Separate cursors for each resource type
    papers_next_cursor: str | None = None
    posts_next_cursor: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "chain of thought reasoning",
                "tag_filter": "artificial-intelligence",
                "papers": [],
                "posts": [],
                "total_papers": 14,
                "total_posts": 6,
                "papers_next_cursor": "eyJpZCI6IjF...",
                "posts_next_cursor": None,
            }
        }
    }


class TaxonomyCategoryResponse(BaseModel):
    slug: str
    label: str
    description: str
    subtopics: list[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "slug": "artificial-intelligence",
                "label": "Artificial Intelligence",
                "description": "Machine learning, deep learning, neural networks, and AI systems",
                "subtopics": ["machine-learning", "deep-learning", "reinforcement-learning"],
            }
        }
    }
