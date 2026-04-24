"""
Ask AI — scoped chat about a specific paper using Gemini 2.5 Flash-Lite.

Isolation note: this is the only file that touches the Gemini client.
To swap providers, change GEMINI_BASE_URL + GEMINI_MODEL in .env and restart.
The openai SDK is used with a custom base_url so no vendor-specific SDK is needed.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.paper import Paper

router = APIRouter(prefix="/api/ask-ai", tags=["ask-ai"])
settings = get_settings()


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="The user's question")
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
        description="Prior turns in the conversation — not persisted by the server",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What dataset did they use to evaluate chain-of-thought prompting?",
                "history": [],
            }
        }
    }


class ChatResponse(BaseModel):
    response: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "The authors evaluated their approach on three benchmarks: BIG-Bench Hard, GSM8K (grade-school math), and MATH. GSM8K contains ~8,500 grade-school math word problems, while MATH is a harder competition-level dataset with ~12,500 problems across seven difficulty levels..."
            }
        }
    }


@router.post(
    "/{paper_id}/chat",
    response_model=ChatResponse,
    summary="Ask a question about a paper — powered by Gemini 2.5 Flash-Lite",
)
async def chat_about_paper(
    paper_id: UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.plain_summary and not paper.technical_summary:
        raise HTTPException(
            status_code=422,
            detail="This paper has not been summarized yet — Ask AI is unavailable until ingestion completes.",
        )

    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="Ask AI is not configured on this server")

    system_prompt = (
        "You are a friendly, knowledgeable research assistant. "
        "Answer questions about the paper below accurately and clearly. "
        "Stay focused on the paper's content. "
        "If you don't know something from the provided summaries, say so honestly.\n\n"
        f"**Title:** {paper.title}\n"
        f"**Authors:** {', '.join(paper.authors or [])}\n\n"
        f"**Plain-language summary:**\n{paper.plain_summary or '(not available)'}\n\n"
        f"**Technical summary:**\n{paper.technical_summary or '(not available)'}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for turn in body.history:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": body.message})

    client = AsyncOpenAI(api_key=settings.google_api_key, base_url=settings.gemini_base_url)

    try:
        completion = await client.chat.completions.create(
            model=settings.gemini_model,
            messages=messages,
        )
        reply = completion.choices[0].message.content or ""
    except Exception as exc:
        # Surface a useful message — common cause is exhausted free-tier quota
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {exc}")

    return ChatResponse(response=reply)
