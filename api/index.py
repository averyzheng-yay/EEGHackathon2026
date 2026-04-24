"""
Vercel serverless entry point.

Vercel's Python runtime picks up the `app` ASGI callable from this file.
All routes are defined in app/main.py — this file just re-exports the app.
"""
from app.main import app  # noqa: F401 — re-exported as the Vercel handler

handler = app
