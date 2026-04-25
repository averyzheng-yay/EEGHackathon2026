"""
Paper summarizer — provider-agnostic via the OpenAI SDK.

Current provider: Cerebras (https://api.cerebras.ai/v1)
Free tier:        ~1M tokens/day (~3,300 summaries), 30 RPM
Model:            llama-3.3-70b

To swap providers: change SUMMARIZER_BASE_URL + SUMMARIZER_MODEL in .env.

Rate-limit policy:
  - Stays under INGESTION_RATE_LIMIT_RPM (default 15)
  - 429 responses trigger exponential backoff: 10 s, 20 s, 40 s
  - After max retries the paper is skipped; the pipeline does not crash
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
    """Enforces a minimum interval between requests to stay within RPM cap."""

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
    Call the summarizer model to generate both summary variants and extract tags.

    Returns (plain_summary, technical_summary, tags).
    Returns (None, None, []) on any failure so the pipeline can skip gracefully.
    """
    if not settings.summarizer_api_key:
        logger.warning("SUMMARIZER_API_KEY not set — skipping summarization")
        return None, None, []

    client = AsyncOpenAI(
        api_key=settings.summarizer_api_key,
        base_url=settings.summarizer_base_url,
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
                model=settings.summarizer_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content or ""
            return _parse_llm_response(content)

        except RateLimitError:
            backoff = 10 * (2 ** attempt)
            logger.warning(
                "Rate limited — backing off %ds (attempt %d/%d)",
                backoff, attempt + 1, max_retries,
            )
            await asyncio.sleep(backoff)

        except Exception as exc:
            logger.error(
                "Summarization failed for %r (attempt %d/%d): %s",
                title[:60], attempt + 1, max_retries, exc,
            )
            if attempt == max_retries - 1:
                return None, None, []

    return None, None, []


def _parse_llm_response(content: str) -> tuple[str | None, str | None, list[str]]:
    """
    Extract summaries and tags from the LLM's JSON response.
    Falls back to storing raw text as plain_summary if JSON parsing fails.
    """
    clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(clean)
        plain = data.get("plain_summary") or None
        technical = data.get("technical_summary") or None
        raw_tags = data.get("tags", [])
        valid_tags = [t for t in raw_tags if t in ALL_TAGS][:8]
        return plain, technical, valid_tags
    except json.JSONDecodeError:
        logger.warning("Could not parse LLM response as JSON; storing as plain_summary")
        return content[:2000] if content else None, None, []
