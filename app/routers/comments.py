"""
Flat comment threads on discussion posts.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentResponse, CreateCommentRequest
from app.schemas.post import PostAuthor

router = APIRouter(prefix="/api/posts", tags=["comments"])


def _to_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author=PostAuthor(id=comment.author.id, username=comment.author.username) if comment.author else None,
        body=comment.body,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get(
    "/{post_id}/comments",
    response_model=list[CommentResponse],
    summary="List all comments on a post (flat, chronological)",
)
async def list_comments(
    post_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    post_check = await db.execute(select(Post.id).where(Post.id == post_id))
    if not post_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    comments = result.scalars().all()
    # Eagerly load authors
    for c in comments:
        await db.refresh(c, ["author"])
    return [_to_response(c) for c in comments]


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a post (requires login)",
)
async def create_comment(
    post_id: UUID,
    body: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(post_id=post_id, author_id=current_user.id, body=body.body)
    db.add(comment)
    post.comment_count += 1
    await db.flush()
    await db.refresh(comment, ["author"])
    await db.commit()
    return _to_response(comment)


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=204,
    summary="Delete a comment (author only)",
)
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    post_result = await db.execute(select(Post).where(Post.id == post_id))
    post = post_result.scalar_one_or_none()
    if post:
        post.comment_count = max(0, post.comment_count - 1)

    await db.delete(comment)
    await db.commit()
