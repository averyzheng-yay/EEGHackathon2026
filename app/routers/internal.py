"""
Internal routes triggered by Vercel Cron Jobs (or manually by the dev team).

⚠️  Vercel Cron Jobs require a Pro plan.  For the free tier, trigger these
    endpoints manually with curl or a third-party cron service (e.g. cron-job.org).

    Protection: X-Internal-Secret header must match INTERNAL_API_SECRET env var.
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends

from app.auth.dependencies import verify_internal
from app.database import AsyncSessionLocal
from app.ingestion.pipeline import run_ingestion
from app.recommendations.scorer import recompute_all_scores

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/internal", tags=["internal"])


@router.post(
    "/ingest",
    summary="Trigger daily paper ingestion from arXiv (Vercel Cron: 02:00 UTC)",
    dependencies=[Depends(verify_internal)],
)
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """
    Kicks off the arXiv → Qwen ingestion pipeline in a background task so the
    cron job gets an immediate 200 response and doesn't time out.
    """
    background_tasks.add_task(_run_ingestion_task)
    return {"status": "ingestion started", "detail": "running in background"}


async def _run_ingestion_task():
    async with AsyncSessionLocal() as db:
        try:
            await run_ingestion(db)
        except Exception:
            logger.exception("Ingestion pipeline failed")


@router.post(
    "/recompute-recommendations",
    summary="Recompute recommendation scores for all active users (Vercel Cron: 03:00 UTC)",
    dependencies=[Depends(verify_internal)],
)
async def trigger_recompute(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_recompute_task)
    return {"status": "recompute started", "detail": "running in background"}


async def _run_recompute_task():
    async with AsyncSessionLocal() as db:
        try:
            await recompute_all_scores(db)
        except Exception:
            logger.exception("Recommendation recompute failed")
