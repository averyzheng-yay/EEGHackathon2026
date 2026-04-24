"""
Qwen-based paper summarizer (DashScope international endpoint).

Rate-limit policy:
  - 10 RPM cap on the free tier → 6 s minimum between requests
  - 429 responses trigger exponential backoff: 10 s, 20 s, 40 s
  - After max retries the paper is skipped (logged); the pipeline does not crash

Both the openai SDK's base_url and the model are configured via .env so the
LLM provider can be swapped without touching this file.
"""
import asyncio
import json
import logging
import time

from openai import AsyncOpenAI, RateLimitError

from app.config import get_settings
from app.taxonomy import ALL_TAGS

logger = logging.getLogger(__name__)
settings = get_settings()

# Pre-built tag list for the LLM prompt — keep it compact
_TAGS_STR = ", ".join(ALL_TAGS)

_SUMMARIZE_PROMPT_TEMPLATE = """\
You are a scientific paper analyst. Given the paper details below, produce two \
summaries and select relevant tags.

Paper title: {title}
Authors: {authors}
Abstract: {abstract}

Respond ONLY with a JSON object (no markdown fences) in this exact shape:
{{
  "plain_summary": "<plain-language summary for a curious general audience, ~150 words, no jargon>",
  "technical_summary": "<technical summary for expert readers using precise terminology, ~200 words>",
  "tags": ["<tag1>", "<tag2>"]
}}

Choose up to 8 tags from this list ONLY:
{tags}
"""


class _RateLimiter:
    """Ensures at most `rpm` calls per minute by enforcing a minimum interval."""

    def __init__(self, rpm: int) -> None:
        self._interval = 60.0 / rpm
        self._last: float = 0.0

    async def wait(self) -> None:
        now = time.monotonic()
        wait = self._interval - (now - self._last)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last = time.monotonic()


_rate_limiter = _RateLimiter(settings.ingestion_rate_limit_rpm)


async def summarize_paper(
    title: str,
    abstract: str,
    authors: list[str],
    max_retries: int = 3,
) -> tuple[str | None, str | None, list[str]]:
    """
    Call Qwen to generate both summaries and extract tags.

    Returns (plain_summary, technical_summary, tags).
    Returns (None, None, []) on failure so the caller can skip gracefully.
    """
    if not settings.dashscope_api_key:
        logger.warning("DASHSCOPE_API_KEY not set — skipping summarization")
        return None, None, []

    client = AsyncOpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
    )
    prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
        title=title,
        authors=", ".join(authors) if authors else "Unknown",
        abstract=abstract or "(no abstract available)",
        tags=_TAGS_STR,
    )

    for attempt in range(max_retries):
        await _rate_limiter.wait()
        try:
            response = await client.chat.completions.create(
                model=settings.qwen_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content or ""
            return _parse_llm_response(content)

        except RateLimitError:
            backoff = 10 * (2 ** attempt)
            logger.warning("Qwen rate limited — backing off %ds (attempt %d/%d)", backoff, attempt + 1, max_retries)
            await asyncio.sleep(backoff)

        except Exception as exc:
            logger.error("Qwen summarization failed for %r (attempt %d/%d): %s", title[:60], attempt + 1, max_retries, exc)
            if attempt == max_retries - 1:
                return None, None, []

    return None, None, []


def _parse_llm_response(content: str) -> tuple[str | None, str | None, list[str]]:
    """
    Extract summaries and tags from the LLM JSON response.
    Falls back to raw text as plain_summary if JSON parsing fails.
    """
    # Strip potential markdown fences the model sneaks in despite instructions
    clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(clean)
        plain = data.get("plain_summary") or None
        technical = data.get("technical_summary") or None
        raw_tags = data.get("tags", [])
        valid_tags = [t for t in raw_tags if t in ALL_TAGS][:8]
        return plain, technical, valid_tags
    except json.JSONDecodeError:
        # Last-resort: treat the whole response as a plain summary
        logger.warning("Could not parse LLM response as JSON; storing as plain_summary")
        return content[:2000] if content else None, None, []
