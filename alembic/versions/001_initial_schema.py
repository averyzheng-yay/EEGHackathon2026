"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-04-24

Creates all tables, enums, indexes (including pg_trgm + full-text GIN indexes),
and partial unique constraints for the votes table.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── Enums ─────────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE expertiselevel AS ENUM ('beginner', 'intermediate', 'expert')")
    op.execute("CREATE TYPE technicallevel AS ENUM ('beginner', 'intermediate', 'expert')")
    op.execute("CREATE TYPE targettype AS ENUM ('paper', 'post')")
    op.execute("CREATE TYPE votetype AS ENUM ('up', 'down')")

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("expertise_level", sa.Enum("beginner", "intermediate", "expert", name="expertiselevel"), nullable=False, server_default="beginner"),
        sa.Column("onboarding_complete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # ── user_interests ────────────────────────────────────────────────────────
    op.create_table(
        "user_interests",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_slug", sa.String(100), primary_key=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ── papers ────────────────────────────────────────────────────────────────
    op.create_table(
        "papers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("arxiv_id", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("plain_summary", sa.Text(), nullable=True),
        sa.Column("technical_summary", sa.Text(), nullable=True),
        sa.Column("tags", ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("primary_category", sa.String(50), nullable=True),
        sa.Column("upvote_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("downvote_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("arxiv_url", sa.String(255), nullable=True),
    )
    op.create_index("ix_papers_arxiv_id", "papers", ["arxiv_id"])
    op.create_index("ix_papers_ingested_at", "papers", ["ingested_at"])
    # GIN index on tags array for fast @> (contains) queries
    op.execute("CREATE INDEX ix_papers_tags ON papers USING gin(tags)")
    # Full-text search index
    op.execute(
        "CREATE INDEX ix_papers_fts ON papers USING gin("
        "  to_tsvector('english',"
        "    coalesce(title,'') || ' ' ||"
        "    coalesce(plain_summary,'') || ' ' ||"
        "    coalesce(technical_summary,'') || ' ' ||"
        "    array_to_string(tags,' ')"
        "  )"
        ")"
    )
    # Trigram index for ILIKE / similarity search on title
    op.execute("CREATE INDEX ix_papers_title_trgm ON papers USING gin(title gin_trgm_ops)")

    # ── posts ─────────────────────────────────────────────────────────────────
    op.create_table(
        "posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("technical_level", sa.Enum("beginner", "intermediate", "expert", name="technicallevel"), nullable=False, server_default="intermediate"),
        sa.Column("tags", ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("upvote_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("downvote_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_posts_author_id", "posts", ["author_id"])
    op.create_index("ix_posts_paper_id", "posts", ["paper_id"])
    op.create_index("ix_posts_created_at", "posts", ["created_at"])
    op.execute("CREATE INDEX ix_posts_tags ON posts USING gin(tags)")
    op.execute(
        "CREATE INDEX ix_posts_fts ON posts USING gin("
        "  to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body,''))"
        ")"
    )
    op.execute("CREATE INDEX ix_posts_title_trgm ON posts USING gin(title gin_trgm_ops)")

    # ── comments ──────────────────────────────────────────────────────────────
    op.create_table(
        "comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("post_id", UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])

    # ── votes ─────────────────────────────────────────────────────────────────
    op.create_table(
        "votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("target_type", sa.Enum("paper", "post", name="targettype"), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=False),
        sa.Column("vote_type", sa.Enum("up", "down", name="votetype"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_votes_user_id", "votes", ["user_id"])
    op.create_index("ix_votes_session_id", "votes", ["session_id"])
    op.create_index("ix_votes_target", "votes", ["target_type", "target_id"])

    # Partial unique constraints prevent duplicate votes
    op.execute(
        "CREATE UNIQUE INDEX uq_votes_user ON votes (user_id, target_type, target_id) "
        "WHERE user_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_votes_session ON votes (session_id, target_type, target_id) "
        "WHERE session_id IS NOT NULL AND user_id IS NULL"
    )

    # ── recommendation_scores ─────────────────────────────────────────────────
    op.create_table(
        "recommendation_scores",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rec_scores_user_score", "recommendation_scores", ["user_id", "score"])


def downgrade() -> None:
    op.drop_table("recommendation_scores")
    op.drop_table("votes")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("papers")
    op.drop_table("refresh_tokens")
    op.drop_table("user_interests")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS votetype")
    op.execute("DROP TYPE IF EXISTS targettype")
    op.execute("DROP TYPE IF EXISTS technicallevel")
    op.execute("DROP TYPE IF EXISTS expertiselevel")
