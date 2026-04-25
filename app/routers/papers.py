"""
Papers feed ("Reels"), paper detail, voting, and view tracking.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.database import get_db
from app.models.paper import Paper
from app.models.recommendation import RecommendationScore
from app.models.user import User
from app.models.vote import TargetType, Vote, VoteType
from app.models.post import Post
from app.schemas.common import decode_cursor, encode_cursor
from app.schemas.paper import PaperCard, PaperDetail, PaperFeed, VoteRequest, VoteResponse
from app.schemas.post import LinkedPaperSnippet, PostCard, PostAuthor

router = APIRouter(prefix="/api/papers", tags=["papers"])

DEFAULT_LIMIT = 20
MAX_LIMIT = 50


def _paper_to_card(paper: Paper) -> PaperCard:
    return PaperCard(
        id=paper.id,
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        authors=paper.authors or [],
        year=paper.year,
        tags=paper.tags or [],
        primary_category=paper.primary_category,
        plain_summary=paper.plain_summary,
        technical_summary=paper.technical_summary,
        upvote_count=paper.upvote_count,
        downvote_count=paper.downvote_count,
        view_count=paper.view_count,
        published_at=paper.published_at,
        arxiv_url=paper.arxiv_url,
    )


@router.get(
    "",
    response_model=PaperFeed,
    summary="Paginated papers feed ('Reels') — personalized for logged-in users",
)
async def get_papers_feed(
    cursor: str | None = Query(None, description="Opaque pagination cursor"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    tag: str | None = Query(None, description="Filter by a taxonomy tag slug"),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    limit = min(limit, MAX_LIMIT)

    if current_user and current_user.onboarding_complete:
        papers, next_cursor = await _personalized_feed(db, current_user.id, cursor, limit, tag)
        # Cold-start: no recommendation scores computed yet — fall back to top-voted
        if not papers:
            papers, next_cursor = await _top_voted_feed(db, cursor, limit, tag)
    else:
        papers, next_cursor = await _top_voted_feed(db, cursor, limit, tag)

    items = [_paper_to_card(p) for p in papers]
    return PaperFeed(items=items, next_cursor=next_cursor, has_more=next_cursor is not None)


async def _personalized_feed(
    db: AsyncSession, user_id: UUID, cursor: str | None, limit: int, tag: str | None
) -> tuple[list[Paper], str | None]:
    """Return papers ordered by recommendation score descending."""
    cursor_data = decode_cursor(cursor) if cursor else {}
    score_lt = cursor_data.get("score", float("inf"))
    paper_id_lt = cursor_data.get("paper_id")

    q = (
        select(Paper, RecommendationScore.score)
        .join(RecommendationScore, (RecommendationScore.paper_id == Paper.id) & (RecommendationScore.user_id == user_id))
    )
    if tag:
        q = q.where(Paper.tags.contains([tag]))

    # Keyset pagination on (score DESC, paper_id ASC)
    if paper_id_lt:
        q = q.where(
            (RecommendationScore.score < score_lt)
            | ((RecommendationScore.score == score_lt) & (Paper.id > paper_id_lt))
        )
    q = q.order_by(RecommendationScore.score.desc(), Paper.id.asc()).limit(limit + 1)

    rows = (await db.execute(q)).all()
    papers = [row[0] for row in rows]

    if len(papers) > limit:
        papers = papers[:limit]
        last = rows[limit - 1]
        next_cursor = encode_cursor({"score": last[1], "paper_id": str(last[0].id)})
    else:
        next_cursor = None

    return papers, next_cursor


async def _top_voted_feed(
    db: AsyncSession, cursor: str | None, limit: int, tag: str | None
) -> tuple[list[Paper], str | None]:
    """Cold-start feed ordered by net votes descending."""
    cursor_data = decode_cursor(cursor) if cursor else {}
    votes_lt = cursor_data.get("votes", float("inf"))
    paper_id_lt = cursor_data.get("paper_id")

    net_votes = (Paper.upvote_count - Paper.downvote_count).label("net_votes")
    q = select(Paper, net_votes)
    if tag:
        q = q.where(Paper.tags.contains([tag]))

    if paper_id_lt:
        q = q.where(
            (net_votes < votes_lt) | ((net_votes == votes_lt) & (Paper.id > paper_id_lt))
        )
    q = q.order_by(net_votes.desc(), Paper.id.asc()).limit(limit + 1)

    rows = (await db.execute(q)).all()
    papers = [row[0] for row in rows]

    if len(papers) > limit:
        papers = papers[:limit]
        last = rows[limit - 1]
        next_cursor = encode_cursor({"votes": last[1], "paper_id": str(last[0].id)})
    else:
        next_cursor = None

    return papers, next_cursor


@router.get("/{paper_id}", response_model=PaperDetail, summary="Full paper detail with linked discussions")
async def get_paper(paper_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Fetch linked discussion posts with authors for the sidebar
    post_result = await db.execute(
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.paper_id == paper_id)
        .order_by(Post.upvote_count.desc())
        .limit(10)
    )
    linked_posts_raw = post_result.scalars().all()

    linked_posts = [
        {
            "id": str(p.id),
            "title": p.title,
            "author_username": p.author.username if p.author else None,
            "comment_count": p.comment_count,
            "upvote_count": p.upvote_count,
        }
        for p in linked_posts_raw
    ]

    return PaperDetail(
        id=paper.id,
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        authors=paper.authors or [],
        year=paper.year,
        abstract=paper.abstract,
        tags=paper.tags or [],
        primary_category=paper.primary_category,
        plain_summary=paper.plain_summary,
        technical_summary=paper.technical_summary,
        upvote_count=paper.upvote_count,
        downvote_count=paper.downvote_count,
        view_count=paper.view_count,
        published_at=paper.published_at,
        ingested_at=paper.ingested_at,
        arxiv_url=paper.arxiv_url,
        linked_posts=linked_posts,
    )


@router.post("/{paper_id}/vote", response_model=VoteResponse, summary="Upvote or downvote a paper")
async def vote_paper(
    paper_id: UUID,
    body: VoteRequest,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    user_id = current_user.id if current_user else None
    session_id = body.session_id if not current_user else None

    if not user_id and not session_id:
        raise HTTPException(status_code=400, detail="Provide session_id for anonymous voting")

    # Find existing vote
    q = select(Vote).where(
        Vote.target_type == TargetType.paper,
        Vote.target_id == paper_id,
    )
    if user_id:
        q = q.where(Vote.user_id == user_id)
    else:
        q = q.where(Vote.session_id == session_id)

    existing_vote = (await db.execute(q)).scalar_one_or_none()
    new_vote_type = VoteType(body.vote_type)

    if existing_vote:
        if existing_vote.vote_type == new_vote_type:
            # Toggling the same vote → remove it
            if existing_vote.vote_type == VoteType.up:
                paper.upvote_count = max(0, paper.upvote_count - 1)
            else:
                paper.downvote_count = max(0, paper.downvote_count - 1)
            await db.delete(existing_vote)
            user_vote = None
        else:
            # Changing vote direction
            if existing_vote.vote_type == VoteType.up:
                paper.upvote_count = max(0, paper.upvote_count - 1)
                paper.downvote_count += 1
            else:
                paper.downvote_count = max(0, paper.downvote_count - 1)
                paper.upvote_count += 1
            existing_vote.vote_type = new_vote_type
            user_vote = body.vote_type
    else:
        db.add(Vote(
            user_id=user_id,
            session_id=session_id,
            target_type=TargetType.paper,
            target_id=paper_id,
            vote_type=new_vote_type,
        ))
        if new_vote_type == VoteType.up:
            paper.upvote_count += 1
        else:
            paper.downvote_count += 1
        user_vote = body.vote_type

    await db.commit()
    return VoteResponse(
        upvote_count=paper.upvote_count,
        downvote_count=paper.downvote_count,
        user_vote=user_vote,
    )


@router.post("/{paper_id}/view", status_code=204, summary="Record a paper view (increments view count)")
async def record_paper_view(paper_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    paper.view_count += 1
    await db.commit()
