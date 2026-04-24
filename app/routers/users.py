"""
User profile routes: current user, public profiles, and onboarding.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import ExpertiseLevel, User, UserInterest
from app.schemas.user import (
    OnboardingRequest,
    UpdateUserRequest,
    UserInterestItem,
    UserMe,
    UserPublic,
)
from app.taxonomy import ALL_TAGS

router = APIRouter(prefix="/api/users", tags=["users"])


def _to_user_me(user: User) -> UserMe:
    return UserMe(
        id=user.id,
        email=user.email,
        username=user.username,
        expertise_level=user.expertise_level.value,
        onboarding_complete=user.onboarding_complete,
        interests=[UserInterestItem(tag_slug=i.tag_slug, priority=i.priority) for i in user.interests],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/me", response_model=UserMe, summary="Get current user's full profile")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.refresh(current_user, ["interests"])
    return _to_user_me(current_user)


@router.patch("/me", response_model=UserMe, summary="Update expertise level or interests")
async def update_me(
    body: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.expertise_level:
        current_user.expertise_level = ExpertiseLevel(body.expertise_level)

    if body.interests is not None:
        invalid = [t for t in body.interests if t not in ALL_TAGS]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Unknown tags: {invalid}")

        # Replace interests
        await db.execute(
            select(UserInterest).where(UserInterest.user_id == current_user.id)
        )
        for old in current_user.interests:
            await db.delete(old)

        for priority, slug in enumerate(body.interests[:10], start=1):
            db.add(UserInterest(user_id=current_user.id, tag_slug=slug, priority=priority))

    await db.commit()
    await db.refresh(current_user, ["interests"])
    return _to_user_me(current_user)


@router.post("/me/onboarding", response_model=UserMe, summary="Complete onboarding after signup")
async def complete_onboarding(
    body: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invalid = [t for t in body.interests if t not in ALL_TAGS]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unknown tags: {invalid}")

    current_user.expertise_level = ExpertiseLevel(body.expertise_level)
    current_user.onboarding_complete = True

    # Clear any prior interests and set the top-5 seed
    for old in current_user.interests:
        await db.delete(old)

    for priority, slug in enumerate(body.interests[:10], start=1):
        db.add(UserInterest(user_id=current_user.id, tag_slug=slug, priority=priority))

    await db.commit()
    await db.refresh(current_user, ["interests"])
    return _to_user_me(current_user)


@router.get("/{username}", response_model=UserPublic, summary="Get public profile by username")
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic(
        id=user.id,
        username=user.username,
        expertise_level=user.expertise_level.value,
        created_at=user.created_at,
    )
