from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.post import PostAuthor


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    author: PostAuthor | None
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "c1d2e3f4-a5b6-7890-cdef-123456789abc",
                "post_id": "a2b3c4d5-e6f7-8901-abcd-ef1234567890",
                "author": {"id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "username": "riya_reads"},
                "body": "Super interesting point — I think the MATH benchmark results are the real story here. The jump from 40% to 72% accuracy just by adding 'Let's think step by step' is wild.",
                "created_at": "2024-04-17T15:04:00Z",
                "updated_at": "2024-04-17T15:04:00Z",
            }
        },
    }


class CreateCommentRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)

    model_config = {
        "json_schema_extra": {
            "example": {"body": "Super interesting point — I think the MATH benchmark results are the real story here."}
        }
    }
