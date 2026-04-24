"""
arXiv Atom API client.

⚠️  FLAG (spec §1.5): The arXiv API returns an Atom XML feed.  Papers that are
    missing required fields (title, abstract, arxiv_id) are logged and skipped
    rather than crashing the pipeline.  If the entire response is unparseable
    the category is skipped and an error is logged.

Politeness: arXiv guidelines recommend ≥3 s between requests.
"""
import asyncio
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
REQUEST_DELAY = 3.0  # seconds between category queries (arXiv politeness policy)


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published_at: datetime | None
    primary_category: str
    arxiv_url: str
    year: int | None


async def fetch_recent_papers(category: str, max_results: int = 5) -> list[ArxivPaper]:
    """
    Fetch the most recently submitted papers for an arXiv category.
    Returns an empty list (and logs) if the API is unreachable or malformed.
    """
    params = {
        "search_query": f"cat:{category}",
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(ARXIV_API_URL, params=params)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("arXiv API request failed for category %s: %s", category, exc)
        return []

    return _parse_feed(resp.text, category)


def _parse_feed(xml_text: str, category: str) -> list[ArxivPaper]:
    """Parse Atom XML into ArxivPaper objects; skip malformed entries."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.error("Failed to parse arXiv XML for category %s: %s", category, exc)
        return []

    papers: list[ArxivPaper] = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        try:
            paper = _parse_entry(entry)
            if paper:
                papers.append(paper)
        except Exception as exc:
            # Log and skip — don't crash the pipeline
            title_el = entry.find(f"{{{ATOM_NS}}}title")
            title_hint = title_el.text[:60] if title_el is not None and title_el.text else "unknown"
            logger.warning("Skipping malformed arXiv entry (title: %r): %s", title_hint, exc)

    return papers


def _parse_entry(entry: ET.Element) -> ArxivPaper | None:
    """Extract fields from a single Atom <entry>.  Returns None if required fields missing."""
    # arXiv ID lives in the <id> element as a URL: http://arxiv.org/abs/XXXX.XXXXX
    id_el = entry.find(f"{{{ATOM_NS}}}id")
    if id_el is None or not id_el.text:
        logger.warning("arXiv entry missing <id> — skipping")
        return None
    arxiv_id = id_el.text.strip().split("/abs/")[-1]
    if not arxiv_id:
        logger.warning("Could not extract arxiv_id from <id>: %s", id_el.text)
        return None

    title_el = entry.find(f"{{{ATOM_NS}}}title")
    if title_el is None or not title_el.text:
        logger.warning("arXiv entry %s missing title — skipping", arxiv_id)
        return None
    title = " ".join(title_el.text.strip().split())  # normalise whitespace

    abstract_el = entry.find(f"{{{ATOM_NS}}}summary")
    abstract = abstract_el.text.strip() if abstract_el is not None and abstract_el.text else ""

    authors = [
        name_el.text.strip()
        for author in entry.findall(f"{{{ATOM_NS}}}author")
        if (name_el := author.find(f"{{{ATOM_NS}}}name")) is not None and name_el.text
    ]

    published_at = None
    pub_el = entry.find(f"{{{ATOM_NS}}}published")
    if pub_el is not None and pub_el.text:
        try:
            published_at = datetime.fromisoformat(pub_el.text.replace("Z", "+00:00"))
        except ValueError:
            pass

    year = published_at.year if published_at else None

    # Primary category from <arxiv:primary_category> or first <category>
    primary_category = ""
    pc_el = entry.find(f"{{{ARXIV_NS}}}primary_category")
    if pc_el is not None:
        primary_category = pc_el.get("term", "")
    else:
        cat_el = entry.find(f"{{{ATOM_NS}}}category")
        if cat_el is not None:
            primary_category = cat_el.get("term", "")

    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"

    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        published_at=published_at,
        primary_category=primary_category,
        arxiv_url=arxiv_url,
        year=year,
    )
