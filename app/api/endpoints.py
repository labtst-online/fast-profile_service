import logging

from auth_lib.auth import CurrentUserUUID  # Import the type alias
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_session
from app.models.profile import Profile
from app.schemas.profile import ProfileRead, ProfileUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/me",
    response_model=ProfileRead,
    summary="Get current user's profile",
    description="Retrieves the profile associated with the authenticated user.",
)
async def get_my_profile(
    user_id: CurrentUserUUID, # Use the dependency alias
    session: AsyncSession = Depends(get_async_session),
):
    """Fetches the profile for the user identified by the JWT."""
    statement = select(Profile).where(Profile.user_id == user_id)
    result = await session.execute(statement)
    profile = result.scalar_one_or_none()

    if not profile:
        logger.info(f"Profile not found for user_id: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    logger.info(f"Retrieved profile for user_id: {user_id}")
    return profile


@router.put(
    "/me",
    response_model=ProfileRead,
    summary="Create or update current user's profile",
    description=(
        "Creates a profile if one doesn't exist for the authenticated user, "
        "or updates the existing one. Uses PUT for idempotency."
    ),
)
async def create_or_update_my_profile(
    profile_update: ProfileUpdate,
    user_id: CurrentUserUUID, # Use the dependency alias
    session: AsyncSession = Depends(get_async_session),
):
    """Creates or updates the profile for the user identified by the JWT."""
    # Try to fetch existing profile
    statement = select(Profile).where(Profile.user_id == user_id)
    result = await session.execute(statement)
    db_profile = result.scalar_one_or_none()

    if db_profile:
        # --- Update existing profile ---
        logger.info(f"Updating profile for user_id: {user_id}")
        # Get update data, excluding unset fields to allow partial updates
        update_data = profile_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(db_profile, key, value)
        # updated_at is handled by the model/DB config
        session.add(db_profile)
        profile_to_return = db_profile
    else:
        # --- Create new profile ---
        logger.info(f"Creating new profile for user_id: {user_id}")
        # Create a new Profile instance, merging user_id and update data
        create_data = profile_update.model_dump()
        db_profile = Profile(**create_data, user_id=user_id)
        # created_at/updated_at handled by model/DB config
        session.add(db_profile)
        profile_to_return = db_profile

    try:
        await session.commit()
        await session.refresh(profile_to_return)
        logger.info(f"Successfully committed profile changes for user_id: {user_id}")
        return profile_to_return
    except IntegrityError: # Should only happen on create if user_id races, but good practice
        await session.rollback()
        logger.error(f"Integrity error (likely duplicate user_id) for user_id: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile potentially already exists or data conflict.",
        )
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error saving profile for user_id: {user_id} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save profile.",
        )
