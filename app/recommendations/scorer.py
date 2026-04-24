"""
Nightly batch recommendation scorer.

Scoring formula (rule-based, no ML):
  tag_score       = overlap(paper.tags, user.top5_interests) / 5   → weight 0.40
  engagement_score = (upvotes - downvotes) / max_net_votes           → weight 0.35
  history_score   = prior_engagement_bonus                           → weight 0.25

Cold-start: users with no history get tag+engagement scores only.
History signal: if the user upvoted ≥1 paper sharing a tag with the candidate,
                add a proportional bonus (capped at 0.25).

Only papers from the last 90 days and users active in the last 30 days are
included to keep the job fast at MVP scale.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.paper import Paper
from app.models.recommendation import RecommendationScore
from app.models.user import User, UserInterest
from app.models.vote import Vote, VoteType, TargetType

logger = logging.getLogger(__name__)

PAPER_WINDOW_DAYS = 90
USER_ACTIVE_DAYS = 30


async def recompute_all_scores(db: AsyncSession) -> dict:
    """
    Recompute recommendation scores for all active users × recent papers.
    Returns a dict with counts for monitoring.
    """
    cutoff_paper = datetime.now(timezone.utc) - timedelta(days=PAPER_WINDOW_DAYS)
    cutoff_user = datetime.now(timezone.utc) - timedelta(days=USER_ACTIVE_DAYS)

    # Fetch recent papers
    paper_result = await db.execute(
        select(Paper).where(Paper.ingested_at >= cutoff_paper)
    )
    papers = paper_result.scalars().all()
    if not papers:
        logger.info("No recent papers to score")
        return {"users_processed": 0, "scores_written": 0}

    # Compute normalization baseline: max net votes across all recent papers
    max_net = max((p.upvote_count - p.downvote_count) for p in papers) or 1

    # Fetch active users (those who have completed onboarding)
    user_result = await db.execute(
        select(User).where(User.onboarding_complete.is_(True))
    )
    users = user_result.scalars().all()
    logger.info("Scoring %d papers × %d users", len(papers), len(users))

    scores_written = 0

    for user in users:
        await db.refresh(user, ["interests"])
        interest_tags = {i.tag_slug for i in user.interests[:5]}

        # History signal: tags from papers this user has upvoted
        history_result = await db.execute(
            select(Paper.tags)
            .join(Vote, (Vote.target_id == Paper.id) & (Vote.target_type == TargetType.paper))
            .where(Vote.user_id == user.id, Vote.vote_type == VoteType.up)
        )
        upvoted_tag_sets = history_result.scalars().all()
        history_tags: set[str] = set()
        for tag_list in upvoted_tag_sets:
            if tag_list:
                history_tags.update(tag_list)

        rows_to_upsert = []
        for paper in papers:
            score = _compute_score(paper, interest_tags, history_tags, max_net)
            rows_to_upsert.append({
                "user_id": user.id,
                "paper_id": paper.id,
                "score": score,
                "computed_at": datetime.now(timezone.utc),
            })

        if rows_to_upsert:
            stmt = pg_insert(RecommendationScore).values(rows_to_upsert)
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "paper_id"],
                set_={"score": stmt.excluded.score, "computed_at": stmt.excluded.computed_at},
            )
            await db.execute(stmt)
            scores_written += len(rows_to_upsert)

    await db.commit()
    result = {"users_processed": len(users), "scores_written": scores_written}
    logger.info("Recommendation recompute complete: %s", result)
    return result


def _compute_score(
    paper: Paper,
    interest_tags: set[str],
    history_tags: set[str],
    max_net: int,
) -> float:
    """Deterministic weighted score in [0, 1]."""
    paper_tags = set(paper.tags or [])

    # Tag overlap (40%): what fraction of the user's top-5 interests does this paper cover?
    tag_score = (len(paper_tags & interest_tags) / max(len(interest_tags), 1)) * 0.40

    # Engagement (35%): normalised net votes
    net = paper.upvote_count - paper.downvote_count
    engagement_score = max(net / max_net, 0.0) * 0.35

    # History (25%): bonus for overlap with tags of papers the user upvoted
    history_overlap = len(paper_tags & history_tags) / max(len(paper_tags), 1) if paper_tags else 0.0
    history_score = min(history_overlap, 1.0) * 0.25

    return round(tag_score + engagement_score + history_score, 6)
