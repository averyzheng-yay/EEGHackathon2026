"""
Full-text search across papers and posts using PostgreSQL pg_trgm + tsvector.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.paper import Paper
from app.models.post import Post
from app.schemas.paper import PaperCard
from app.schemas.post import LinkedPaperSnippet, PostAuthor, PostCard
from app.schemas.search import SearchResponse, TaxonomyCategoryResponse
from app.taxonomy import TAXONOMY

router = APIRouter(prefix="/api", tags=["search"])

MAX_RESULTS = 20


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
    "/search",
    response_model=SearchResponse,
    summary="Search papers and posts — results split into Papers and Discussions tabs",
)
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    tag: str | None = Query(None, description="Preset topic filter (taxonomy slug)"),
    limit: int = Query(MAX_RESULTS, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    # Build the tsvector search expression for papers
    paper_ts = func.to_tsvector(
        "english",
        func.coalesce(Paper.title, "")
        + " "
        + func.coalesce(Paper.plain_summary, "")
        + " "
        + func.coalesce(Paper.technical_summary, "")
        + " "
        + func.array_to_string(Paper.tags, " "),
    )
    paper_query = func.plainto_tsquery("english", q)
    paper_rank = func.ts_rank(paper_ts, paper_query).label("rank")

    pq = select(Paper, paper_rank).where(
        or_(
            paper_ts.op("@@")(paper_query),
            Paper.title.ilike(f"%{q}%"),
        )
    )
    if tag:
        pq = pq.where(Paper.tags.contains([tag]))
    pq = pq.order_by(paper_rank.desc()).limit(limit)
    paper_rows = (await db.execute(pq)).all()
    paper_items = [_paper_to_card(row[0]) for row in paper_rows]

    # Build search for posts
    post_ts = func.to_tsvector(
        "english",
        func.coalesce(Post.title, "") + " " + func.coalesce(Post.body, ""),
    )
    post_query = func.plainto_tsquery("english", q)
    post_rank = func.ts_rank(post_ts, post_query).label("rank")

    postsq = select(Post, post_rank).where(
        or_(
            post_ts.op("@@")(post_query),
            Post.title.ilike(f"%{q}%"),
        )
    )
    if tag:
        postsq = postsq.where(Post.tags.contains([tag]))
    postsq = postsq.order_by(post_rank.desc()).limit(limit)
    post_rows = (await db.execute(postsq)).all()

    # Batch load linked papers for post cards
    raw_posts = [row[0] for row in post_rows]
    paper_ids = list({p.paper_id for p in raw_posts if p.paper_id})
    papers_by_id: dict = {}
    if paper_ids:
        pr = await db.execute(select(Paper).where(Paper.id.in_(paper_ids)))
        for paper in pr.scalars().all():
            papers_by_id[paper.id] = paper

    for post in raw_posts:
        await db.refresh(post, ["author"])

    post_items = [
        PostCard(
            id=p.id,
            title=p.title,
            author=PostAuthor(id=p.author.id, username=p.author.username) if p.author else None,
            tags=p.tags or [],
            technical_level=p.technical_level.value,
            upvote_count=p.upvote_count,
            downvote_count=p.downvote_count,
            comment_count=p.comment_count,
            created_at=p.created_at,
            linked_paper=LinkedPaperSnippet(
                id=papers_by_id[p.paper_id].id,
                arxiv_id=papers_by_id[p.paper_id].arxiv_id,
                title=papers_by_id[p.paper_id].title,
            ) if p.paper_id and p.paper_id in papers_by_id else None,
        )
        for p in raw_posts
    ]

    return SearchResponse(
        query=q,
        tag_filter=tag,
        papers=paper_items,
        posts=post_items,
        total_papers=len(paper_items),
        total_posts=len(post_items),
    )


@router.get(
    "/tags",
    response_model=list[TaxonomyCategoryResponse],
    summary="List the full tag taxonomy — used for interest selection and filter tabs",
)
async def list_tags():
    return [
        TaxonomyCategoryResponse(
            slug=slug,
            label=data["label"],
            description=data["description"],
            subtopics=data["subtopics"],
        )
        for slug, data in TAXONOMY.items()
    ]
