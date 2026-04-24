"""
Shared pagination and response envelope schemas.

Pagination convention:
  - Requests:  GET /resource?cursor=<opaque>&limit=20
  - Responses: { items: [...], next_cursor: "..." | null, has_more: bool }
  - cursor is a base64-encoded JSON string; treat it as opaque on the frontend.
"""
import base64
import json
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool


def encode_cursor(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()))
    except Exception:
        return {}
