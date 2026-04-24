"""
OLAPIS API — Reddit for research.

Swagger UI: /docs
ReDoc:      /redoc
OpenAPI JSON: /openapi.json
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import ask_ai, auth, comments, internal, papers, posts, search, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="OLAPIS API",
    description=(
        "**Reddit for research** — a platform for research enthusiasts to stay current "
        "with the latest findings in their fields while discussing them with curious people.\n\n"
        "## Auth\n"
        "Most write endpoints require a Bearer token. Obtain one via `POST /api/auth/login`.\n\n"
        "## Pagination\n"
        "Feed endpoints use cursor-based infinite scroll. Pass the `next_cursor` value from "
        "the previous response as the `cursor` query parameter. Treat cursors as opaque strings.\n\n"
        "## Ask AI\n"
        "The `POST /api/ask-ai/{paper_id}/chat` endpoint is scoped to a single paper's "
        "stored summaries. Chat history is managed client-side and passed as `history` in the "
        "request body — nothing is persisted server-side."
    ),
    version="0.1.0",
    contact={"name": "OLAPIS Team"},
    license_info={"name": "MIT"},
)

# CORS — tighten ALLOWED_ORIGINS in production
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(papers.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(search.router)
app.include_router(ask_ai.router)
app.include_router(internal.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"name": "OLAPIS API", "version": "0.1.0", "docs": "/docs"}


@app.get("/health", tags=["health"], summary="Health check")
async def health():
    return {"status": "ok"}
