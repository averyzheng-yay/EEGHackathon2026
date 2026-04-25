"""
Authentication routes: register, login, token refresh, logout.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.database import get_db
from app.models.user import ExpertiseLevel, RefreshToken, User
from app.models.vote import Vote
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest
from app.schemas.user import AuthResponse, UserInterestItem, UserMe

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _build_user_me(user: User) -> UserMe:
    interests = [UserInterestItem(tag_slug=i.tag_slug, priority=i.priority) for i in user.interests]
    return UserMe(
        id=user.id,
        email=user.email,
        username=user.username,
        expertise_level=user.expertise_level.value,
        onboarding_complete=user.onboarding_complete,
        interests=interests,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def _issue_tokens(user: User, db: AsyncSession) -> tuple[str, str]:
    """Create an access token and a persisted refresh token; return both."""
    access = create_access_token(str(user.id), user.username)
    raw_refresh, hashed, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hashed, expires_at=expires_at))
    await db.commit()
    return access, raw_refresh


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    existing = await db.execute(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email or username already taken")

    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
        expertise_level=ExpertiseLevel.beginner,
        onboarding_complete=False,
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    access, raw_refresh = await _issue_tokens(user, db)
    # Explicitly load the relationship — lazy access in async raises MissingGreenlet
    await db.refresh(user, ["interests"])
    return AuthResponse(
        access_token=access,
        refresh_token=raw_refresh,
        user=await _build_user_me(user),
    )


@router.post("/login", response_model=AuthResponse, summary="Log in and receive tokens")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Merge anonymous votes from the session into the user's account
    if body.session_id:
        await _merge_anonymous_votes(db, user.id, body.session_id)

    # Eagerly load interests for the response
    await db.refresh(user, ["interests"])

    access, raw_refresh = await _issue_tokens(user, db)
    return AuthResponse(
        access_token=access,
        refresh_token=raw_refresh,
        user=await _build_user_me(user),
    )


async def _merge_anonymous_votes(db: AsyncSession, user_id, session_id: str) -> None:
    """Transfer session-based anonymous votes to the authenticated user."""
    result = await db.execute(
        select(Vote).where(Vote.session_id == session_id, Vote.user_id.is_(None))
    )
    anon_votes = result.scalars().all()

    for vote in anon_votes:
        # Skip if user already voted on this target (their explicit vote wins)
        conflict = await db.execute(
            select(Vote).where(
                Vote.user_id == user_id,
                Vote.target_type == vote.target_type,
                Vote.target_id == vote.target_id,
            )
        )
        if conflict.scalar_one_or_none() is not None:
            await db.delete(vote)
        else:
            vote.user_id = user_id
            vote.session_id = None

    await db.commit()


@router.post("/refresh", response_model=dict, summary="Rotate refresh token")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    hashed = hash_refresh_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashed,
            RefreshToken.revoked.is_(False),
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record or token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token invalid or expired")

    # Rotate: revoke old, issue new
    token_record.revoked = True
    user_result = await db.execute(select(User).where(User.id == token_record.user_id))
    user = user_result.scalar_one()

    new_access = create_access_token(str(user.id), user.username)
    raw_new, new_hashed, new_expires = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=new_hashed, expires_at=new_expires))
    await db.commit()

    return {"access_token": new_access, "refresh_token": raw_new, "token_type": "bearer"}


@router.post("/logout", status_code=204, summary="Revoke refresh token")
async def logout(body: LogoutRequest, db: AsyncSession = Depends(get_db)):
    hashed = hash_refresh_token(body.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
    token_record = result.scalar_one_or_none()
    if token_record:
        token_record.revoked = True
        await db.commit()
    # Always return 204 — don't leak whether the token existed
