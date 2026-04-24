"""
Daily ingestion orchestrator.

Flow per run:
  1. For each arXiv category in the taxonomy, fetch the N most recent papers.
  2. Skip papers already in the database (idempotent).
  3. Summarize each new paper with Qwen (rate-limited, with backoff).
  4. Persist the paper record.

The pipeline is intentionally forgiving: errors on individual papers are logged
and skipped so a single bad entry never aborts the whole run.
"""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.arxiv_client import REQUEST_DELAY, fetch_recent_papers
from app.ingestion.summarizer import summarize_paper
from app.models.paper import Paper
from app.taxonomy import TAXONOMY
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_ingestion(db: AsyncSession) -> dict:
    """
    Run the full ingestion pipeline for all taxonomy categories.
    Returns a summary dict with counts for monitoring/logging.
    """
    fetched = 0
    new_count = 0
    skipped = 0
    failed = 0

    for category_slug, category_data in TAXONOMY.items():
        for arxiv_category in category_data["arxiv_categories"]:
            logger.info("Fetching from arXiv category: %s", arxiv_category)
            papers = await fetch_recent_papers(arxiv_category, settings.arxiv_papers_per_category)
            fetched += len(papers)

            for arxiv_paper in papers:
                # Skip if already ingested
                existing = await db.execute(
                    select(Paper.id).where(Paper.arxiv_id == arxiv_paper.arxiv_id)
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                logger.info("Summarizing: %s", arxiv_paper.title[:80])
                try:
                    plain_summary, technical_summary, tags = await summarize_paper(
                        title=arxiv_paper.title,
                        abstract=arxiv_paper.abstract,
                        authors=arxiv_paper.authors,
                    )
                except Exception as exc:
                    logger.error("Summarization raised unexpectedly for %s: %s", arxiv_paper.arxiv_id, exc)
                    plain_summary = technical_summary = None
                    tags = []
                    failed += 1

                # Always ensure the parent category tag is included
                if category_slug not in tags:
                    tags = [category_slug] + tags

                paper = Paper(
                    arxiv_id=arxiv_paper.arxiv_id,
                    title=arxiv_paper.title,
                    authors=arxiv_paper.authors,
                    year=arxiv_paper.year,
                    abstract=arxiv_paper.abstract,
                    plain_summary=plain_summary,
                    technical_summary=technical_summary,
                    tags=tags,
                    primary_category=arxiv_paper.primary_category,
                    published_at=arxiv_paper.published_at,
                    arxiv_url=arxiv_paper.arxiv_url,
                )
                db.add(paper)
                try:
                    await db.commit()
                    new_count += 1
                    logger.info("Stored paper: %s", arxiv_paper.arxiv_id)
                except Exception as exc:
                    await db.rollback()
                    logger.error("DB error storing paper %s: %s", arxiv_paper.arxiv_id, exc)
                    failed += 1

            # Politeness delay between category fetches
            await asyncio.sleep(REQUEST_DELAY)

    summary = {
        "fetched": fetched,
        "new": new_count,
        "skipped_existing": skipped,
        "failed": failed,
    }
    logger.info("Ingestion complete: %s", summary)
    return summary
