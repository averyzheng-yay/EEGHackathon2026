"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-04-24

Uses raw SQL via op.execute() throughout so SQLAlchemy never touches enum-type
creation — the root cause of all the DuplicateObjectError failures when mixing
op.create_table() with named PostgreSQL enums.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE expertiselevel AS ENUM ('beginner', 'intermediate', 'expert');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE technicallevel AS ENUM ('beginner', 'intermediate', 'expert');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE targettype AS ENUM ('paper', 'post');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE votetype AS ENUM ('up', 'down');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email           VARCHAR(255) NOT NULL UNIQUE,
            username        VARCHAR(50)  NOT NULL UNIQUE,
            password_hash   VARCHAR(255) NOT NULL,
            expertise_level expertiselevel NOT NULL DEFAULT 'beginner',
            onboarding_complete BOOLEAN NOT NULL DEFAULT false,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email    ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS user_interests (
            user_id    UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tag_slug   VARCHAR(100) NOT NULL,
            priority   INTEGER      NOT NULL DEFAULT 5,
            created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, tag_slug)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id    UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked    BOOLEAN     NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            arxiv_id          VARCHAR(50)  NOT NULL UNIQUE,
            title             TEXT         NOT NULL,
            authors           TEXT[]       NOT NULL DEFAULT '{}',
            year              INTEGER,
            abstract          TEXT,
            plain_summary     TEXT,
            technical_summary TEXT,
            tags              TEXT[]       NOT NULL DEFAULT '{}',
            primary_category  VARCHAR(50),
            upvote_count      INTEGER      NOT NULL DEFAULT 0,
            downvote_count    INTEGER      NOT NULL DEFAULT 0,
            view_count        INTEGER      NOT NULL DEFAULT 0,
            published_at      TIMESTAMPTZ,
            ingested_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
            arxiv_url         VARCHAR(255)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_papers_arxiv_id   ON papers (arxiv_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_papers_ingested_at ON papers (ingested_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_papers_tags ON papers USING gin(tags)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_papers_fts ON papers USING gin(
            to_tsvector('english',
                coalesce(title,'') || ' ' ||
                coalesce(plain_summary,'') || ' ' ||
                coalesce(technical_summary,'')
            )
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_papers_title_trgm ON papers USING gin(title gin_trgm_ops)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            title           VARCHAR(500)   NOT NULL,
            body            TEXT           NOT NULL,
            author_id       UUID           REFERENCES users(id)  ON DELETE SET NULL,
            paper_id        UUID           REFERENCES papers(id) ON DELETE SET NULL,
            technical_level technicallevel NOT NULL DEFAULT 'intermediate',
            tags            TEXT[]         NOT NULL DEFAULT '{}',
            upvote_count    INTEGER        NOT NULL DEFAULT 0,
            downvote_count  INTEGER        NOT NULL DEFAULT 0,
            comment_count   INTEGER        NOT NULL DEFAULT 0,
            view_count      INTEGER        NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ    NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ    NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_author_id  ON posts (author_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_paper_id   ON posts (paper_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_created_at ON posts (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_tags ON posts USING gin(tags)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_posts_fts ON posts USING gin(
            to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body,''))
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_title_trgm ON posts USING gin(title gin_trgm_ops)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            post_id    UUID        NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            author_id  UUID        REFERENCES users(id) ON DELETE SET NULL,
            body       TEXT        NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_post_id   ON comments (post_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_author_id ON comments (author_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id     UUID       REFERENCES users(id) ON DELETE CASCADE,
            session_id  VARCHAR(128),
            target_type targettype NOT NULL,
            target_id   UUID       NOT NULL,
            vote_type   votetype   NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_votes_user_id    ON votes (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_votes_session_id ON votes (session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_votes_target     ON votes (target_type, target_id)")
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_votes_user
        ON votes (user_id, target_type, target_id)
        WHERE user_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_votes_session
        ON votes (session_id, target_type, target_id)
        WHERE session_id IS NOT NULL AND user_id IS NULL
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_scores (
            user_id    UUID        NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
            paper_id   UUID        NOT NULL REFERENCES papers(id)  ON DELETE CASCADE,
            score      FLOAT       NOT NULL DEFAULT 0.0,
            computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, paper_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_rec_scores_user_score ON recommendation_scores (user_id, score)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS recommendation_scores")
    op.execute("DROP TABLE IF EXISTS votes")
    op.execute("DROP TABLE IF EXISTS comments")
    op.execute("DROP TABLE IF EXISTS posts")
    op.execute("DROP TABLE IF EXISTS papers")
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
    op.execute("DROP TABLE IF EXISTS user_interests")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TYPE IF EXISTS votetype")
    op.execute("DROP TYPE IF EXISTS targettype")
    op.execute("DROP TYPE IF EXISTS technicallevel")
    op.execute("DROP TYPE IF EXISTS expertiselevel")
