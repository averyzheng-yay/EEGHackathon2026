# OLAPIS — Reddit for Research

> Stay current with the latest research findings and discuss them with curious people — in one place.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Database | Neon PostgreSQL (serverless) |
| ORM / Migrations | SQLAlchemy 2.0 (async) + Alembic |
| Auth | JWT (access tokens) + opaque refresh tokens |
| Ingestion LLM | Qwen `qwen-long` via DashScope (OpenAI-compatible) |
| Chat LLM | Gemini 2.5 Flash-Lite via Google AI (OpenAI-compatible) |
| Search | PostgreSQL `pg_trgm` + full-text `tsvector` |
| Deployment | Vercel (Python serverless) |

---

## Local Development

### 1. Prerequisites

- Python 3.11+
- A PostgreSQL database (local or [Neon free tier](https://neon.tech))

### 2. Clone and install

```bash
git clone <repo-url>
cd olapis

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in DATABASE_URL, SECRET_KEY, DASHSCOPE_API_KEY, GOOGLE_API_KEY
# See .env.example for descriptions of every variable
```

**Minimum required for local dev:**
- `DATABASE_URL` — your Neon or local Postgres connection string
- `SECRET_KEY` — any random 32-char hex string (`python -c "import secrets; print(secrets.token_hex(32))"`)

**Optional (features degrade gracefully without them):**
- `DASHSCOPE_API_KEY` — paper summarization (ingestion skips summarization without it)
- `GOOGLE_API_KEY` — Ask AI chat (endpoint returns 503 without it)
- `INTERNAL_API_SECRET` — if empty, internal endpoints are unprotected (fine for dev)

### 4. Run database migrations

```bash
alembic upgrade head
```

This creates all tables, enums, and GIN indexes (including `pg_trgm`).

### 5. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now live at **http://localhost:8000**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### 6. Trigger a test ingestion (optional)

```bash
curl -X POST http://localhost:8000/api/internal/ingest
# No secret required when INTERNAL_API_SECRET is empty
```

---

## Deployment to Vercel

### Prerequisites
- Vercel CLI: `npm i -g vercel`
- A Neon PostgreSQL database (free tier works)

### Deploy

```bash
vercel --prod
```

### Environment variables on Vercel

Set all variables from `.env.example` in the Vercel project dashboard under **Settings → Environment Variables**.

> **Note on Cron Jobs:** `vercel.json` defines two cron jobs (ingestion at 02:00 UTC, recommendation recompute at 03:00 UTC). Vercel Cron Jobs require the **Pro plan**. On the free tier, trigger these manually or use a free cron service like [cron-job.org](https://cron-job.org) pointing at your Vercel deployment URL with the `X-Internal-Secret` header.

---

## Frontend Integration Guide (for Vercel v0)

### Base URL

```
Development:  http://localhost:8000
Production:   https://<your-vercel-deployment>.vercel.app
```

### Authentication

All protected endpoints require a `Bearer` token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/auth/login`. Store it in memory (not `localStorage`). Use `POST /api/auth/refresh` to renew it before expiry (30 min default).

### Pagination (Cursor-based Infinite Scroll)

All feed endpoints (`GET /api/papers`, `GET /api/posts`) return:

```json
{
  "items": [...],
  "next_cursor": "eyJzY29yZSI6...",
  "has_more": true
}
```

To load the next page, pass `?cursor=<next_cursor>` on the next request. When `has_more` is `false` or `next_cursor` is `null`, you've reached the end.

```js
// Example fetch
const res = await fetch(`/api/papers?cursor=${nextCursor}&limit=20`, {
  headers: { Authorization: `Bearer ${token}` }
});
const { items, next_cursor, has_more } = await res.json();
```

### Anonymous Voting

Anonymous users can vote. Generate a random `session_id` on the frontend (store in `localStorage`) and pass it with every vote request:

```json
{ "vote_type": "up", "session_id": "anon_sess_abc123" }
```

On login, pass the same `session_id` in the login request body — the server will merge all anonymous votes into the user's account automatically.

### Summary Display by Expertise Level

After onboarding, the user's `expertise_level` is available in `GET /api/users/me`. Use it to decide which summary variant to show:

| Level | Default shown | Toggle available |
|---|---|---|
| `beginner` | `plain_summary` | No |
| `intermediate` | `plain_summary` | Yes — toggle to reveal `technical_summary` |
| `expert` | `technical_summary` | No |

Both fields are always returned in the API — the display logic lives entirely in the frontend.

### Ask AI Modal

The Ask AI feature is available on any post or paper detail page where the paper has summaries. Send `POST /api/ask-ai/{paper_id}/chat` with the current message and prior turns:

```json
{
  "message": "What's the key finding?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

Chat history is **not persisted** server-side — maintain it in component state.

### Key Endpoints Reference

| Method | Path | Auth? | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Create account |
| POST | `/api/auth/login` | ❌ | Login → tokens |
| POST | `/api/auth/refresh` | ❌ | Rotate refresh token |
| GET | `/api/users/me` | ✅ | Current user profile |
| POST | `/api/users/me/onboarding` | ✅ | Complete onboarding |
| GET | `/api/papers` | Optional | Papers feed (Reels) |
| GET | `/api/papers/{id}` | ❌ | Paper detail |
| POST | `/api/papers/{id}/vote` | Optional | Vote on paper |
| GET | `/api/posts` | Optional | Home feed |
| POST | `/api/posts` | ✅ | Create post |
| GET | `/api/posts/{id}` | ❌ | Post detail |
| POST | `/api/posts/{id}/vote` | Optional | Vote on post |
| GET | `/api/posts/{id}/comments` | ❌ | List comments |
| POST | `/api/posts/{id}/comments` | ✅ | Add comment |
| GET | `/api/search?q=...` | ❌ | Search papers + posts |
| GET | `/api/tags` | ❌ | Tag taxonomy |
| POST | `/api/ask-ai/{id}/chat` | ❌ | Ask AI about paper |

Full spec with schemas: `GET /openapi.json` (or `/docs` for interactive UI).

---

## Architecture Notes

### Data Pipeline

```
arXiv Atom API
    ↓  (daily, per taxonomy category)
arxiv_client.py — fetches & parses XML, skips malformed entries (⚠ FLAG: §1.5)
    ↓
summarizer.py — Qwen qwen-long via DashScope
              — rate-limited to 10 RPM
              — exponential backoff on 429s
              — produces plain_summary + technical_summary + tags
    ↓
PostgreSQL (Neon) — papers table
    ↓  (nightly batch)
scorer.py — recomputes recommendation_scores for active users
```

### Recommendation Algorithm (Rule-based)

```
score = tag_overlap × 0.40
      + engagement    × 0.35
      + user_history  × 0.25
```

- **Tag overlap**: fraction of user's top-5 interest tags that the paper covers
- **Engagement**: normalized net votes (upvotes − downvotes) across recent papers
- **User history**: overlap with tags of papers the user has previously upvoted

Scores are recomputed nightly — not real-time. Cold-start users (no history) are shown top-voted content filtered by their selected interest tags.

### LLM Provider Isolation

Both LLM integrations use the `openai` Python SDK with a custom `base_url`:

- **Qwen** (ingestion): `app/ingestion/summarizer.py` — change `DASHSCOPE_BASE_URL` + `QWEN_MODEL`
- **Gemini** (Ask AI): `app/routers/ask_ai.py` — change `GEMINI_BASE_URL` + `GEMINI_MODEL`

Swap either provider by updating two env vars and redeploying — no code changes needed.

### Database Connection (Serverless)

Neon PostgreSQL is accessed via `asyncpg` with `NullPool` — each Vercel function invocation gets a fresh connection. This avoids connection leaks in serverless environments where there's no persistent process to return connections to a pool.