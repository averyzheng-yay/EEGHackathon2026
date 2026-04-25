"""
Discussion posts: home feed, CRUD, voting, and view tracking.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.database import get_db
from app.models.paper import Paper
from app.models.post import Post, TechnicalLevel
from app.models.user import User
from app.models.vote import TargetType, Vote, VoteType
from app.schemas.common import decode_cursor, encode_cursor
from app.schemas.paper import VoteRequest, VoteResponse
from app.schemas.post import (
    CreatePostRequest,
    LinkedPaperSnippet,
    PostAuthor,
    PostCard,
    PostDetail,
    PostFeed,
    UpdatePostRequest,
)

router = APIRouter(prefix="/api/posts", tags=["posts"])

DEFAULT_LIMIT = 20
MAX_LIMIT = 50


def _post_to_card(post: Post, paper: Paper | None = None) -> PostCard:
    linked = None
    if paper:
        linked = LinkedPaperSnippet(id=paper.id, arxiv_id=paper.arxiv_id, title=paper.title)
    return PostCard(
        id=post.id,
        title=post.title,
        author=PostAuthor(id=post.author.id, username=post.author.username) if post.author else None,
        tags=post.tags or [],
        technical_level=post.technical_level.value,
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        comment_count=post.comment_count,
        created_at=post.created_at,
        linked_paper=linked,
    )


def _post_to_detail(post: Post, paper: Paper | None = None) -> PostDetail:
    linked = None
    if paper:
        linked = LinkedPaperSnippet(id=paper.id, arxiv_id=paper.arxiv_id, title=paper.title)
    return PostDetail(
        id=post.id,
        title=post.title,
        body=post.body,
        author=PostAuthor(id=post.author.id, username=post.author.username) if post.author else None,
        tags=post.tags or [],
        technical_level=post.technical_level.value,
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        comment_count=post.comment_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
        linked_paper=linked,
    )


@router.get(
    "",
    response_model=PostFeed,
    summary="Home feed — top posts globally, or personalized if logged in",
)
async def get_posts_feed(
    cursor: str | None = Query(None),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    tag: str | None = Query(None, description="Filter by tag slug"),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    limit = min(limit, MAX_LIMIT)
    cursor_data = decode_cursor(cursor) if cursor else {}
    votes_lt = cursor_data.get("votes", float("inf"))
    post_id_lt = cursor_data.get("post_id")

    # For MVP, the home feed shows top-voted posts.
    # Personalization of the post feed is a v2 feature (posts don't have recommendation scores).
    net_votes = (Post.upvote_count - Post.downvote_count).label("net_votes")
    q = select(Post, net_votes).options(selectinload(Post.author))
    if tag:
        q = q.where(Post.tags.contains([tag]))
    if post_id_lt:
        q = q.where(
            (net_votes < votes_lt) | ((net_votes == votes_lt) & (Post.id > post_id_lt))
        )
    q = q.order_by(net_votes.desc(), Post.id.asc()).limit(limit + 1)

    rows = (await db.execute(q)).all()
    posts = [row[0] for row in rows]

    # Batch-load linked papers
    paper_ids = list({p.paper_id for p in posts if p.paper_id})
    papers_by_id: dict = {}
    if paper_ids:
        paper_result = await db.execute(select(Paper).where(Paper.id.in_(paper_ids)))
        for paper in paper_result.scalars().all():
            papers_by_id[paper.id] = paper

    # Eagerly load authors (already loaded via relationship if session is fresh)
    next_cursor = None
    if len(posts) > limit:
        posts = posts[:limit]
        last = rows[limit - 1]
        next_cursor = encode_cursor({"votes": last[1], "post_id": str(last[0].id)})

    items = [_post_to_card(p, papers_by_id.get(p.paper_id)) for p in posts]
    return PostFeed(items=items, next_cursor=next_cursor, has_more=next_cursor is not None)


@router.post(
    "",
    response_model=PostDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new discussion post",
)
async def create_post(
    body: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    paper = None
    if body.paper_id:
        paper_result = await db.execute(select(Paper).where(Paper.id == body.paper_id))
        paper = paper_result.scalar_one_or_none()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

    post = Post(
        title=body.title,
        body=body.body,
        author_id=current_user.id,
        paper_id=body.paper_id,
        technical_level=TechnicalLevel(body.technical_level),
        tags=body.tags or [],
    )
    db.add(post)
    await db.commit()
    result2 = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.id == post.id))
    post = result2.scalar_one()
    return _post_to_detail(post, paper)


@router.get("/{post_id}", response_model=PostDetail, summary="Full post detail")
async def get_post(post_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    paper = None
    if post.paper_id:
        paper_result = await db.execute(select(Paper).where(Paper.id == post.paper_id))
        paper = paper_result.scalar_one_or_none()

    return _post_to_detail(post, paper)


@router.patch("/{post_id}", response_model=PostDetail, summary="Edit a post (author only)")
async def update_post(
    post_id: UUID,
    body: UpdatePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if body.title is not None:
        post.title = body.title
    if body.body is not None:
        post.body = body.body
    if body.technical_level is not None:
        post.technical_level = TechnicalLevel(body.technical_level)
    if body.tags is not None:
        post.tags = body.tags

    await db.commit()
    result2 = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.id == post.id))
    post = result2.scalar_one()

    paper = None
    if post.paper_id:
        paper_result = await db.execute(select(Paper).where(Paper.id == post.paper_id))
        paper = paper_result.scalar_one_or_none()

    return _post_to_detail(post, paper)


@router.delete("/{post_id}", status_code=204, summary="Delete a post (author only)")
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.delete(post)
    await db.commit()


@router.post("/{post_id}/vote", response_model=VoteResponse, summary="Upvote or downvote a post")
async def vote_post(
    post_id: UUID,
    body: VoteRequest,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    user_id = current_user.id if current_user else None
    session_id = body.session_id if not current_user else None

    if not user_id and not session_id:
        raise HTTPException(status_code=400, detail="Provide session_id for anonymous voting")

    q = select(Vote).where(Vote.target_type == TargetType.post, Vote.target_id == post_id)
    q = q.where(Vote.user_id == user_id) if user_id else q.where(Vote.session_id == session_id)
    existing_vote = (await db.execute(q)).scalar_one_or_none()
    new_vote_type = VoteType(body.vote_type)

    if existing_vote:
        if existing_vote.vote_type == new_vote_type:
            if existing_vote.vote_type == VoteType.up:
                post.upvote_count = max(0, post.upvote_count - 1)
            else:
                post.downvote_count = max(0, post.downvote_count - 1)
            await db.delete(existing_vote)
            user_vote = None
        else:
            if existing_vote.vote_type == VoteType.up:
                post.upvote_count = max(0, post.upvote_count - 1)
                post.downvote_count += 1
            else:
                post.downvote_count = max(0, post.downvote_count - 1)
                post.upvote_count += 1
            existing_vote.vote_type = new_vote_type
            user_vote = body.vote_type
    else:
        db.add(Vote(
            user_id=user_id,
            session_id=session_id,
            target_type=TargetType.post,
            target_id=post_id,
            vote_type=new_vote_type,
        ))
        if new_vote_type == VoteType.up:
            post.upvote_count += 1
        else:
            post.downvote_count += 1
        user_vote = body.vote_type

    await db.commit()
    return VoteResponse(
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        user_vote=user_vote,
    )


@router.post("/{post_id}/view", status_code=204, summary="Record a post view")
async def record_post_view(post_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.view_count += 1
    await db.commit()
