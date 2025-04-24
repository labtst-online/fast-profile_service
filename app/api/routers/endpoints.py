import logging
from typing import Annotated

from auth_lib.auth import CurrentUserUUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_session
from app.core.s3_client import S3Client
from app.models.profile import Profile
from app.schemas.profile import ProfileRead

logger = logging.getLogger(__name__)
router = APIRouter()

USER_ICON_PREFIX = "icons/"
ICON_URL_EXPIRY_SECONDS = 3600 * 24  # 1 day by default


@router.get(
    "/me",
    response_model=ProfileRead,
    summary="Get current user's profile",
    description="Retrieves the profile associated with the authenticated user.",
)
async def get_my_profile(
    request: Request,
    user_id: CurrentUserUUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Fetches the profile for the user identified by the JWT, including avatar URL from S3."""
    try:
        s3: S3Client = request.app.state.s3_client
    except AttributeError:
        logger.error("S3Client not found in application state. Check lifespan initialization.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 storage service is not configured correctly.",
        )
    # Fetch profile from the database
    statement = select(Profile).where(Profile.user_id == user_id)
    result = await session.execute(statement)
    profile = result.scalar_one_or_none()

    if not profile:
        logger.info(f"Profile not found for user_id: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    avatar_url: str | None = None
    if profile.avatar_url:
        try:
            avatar_url = await s3.get_file_url(
                object_key=profile.avatar_url, expires_in=ICON_URL_EXPIRY_SECONDS
            )
            logger.info(f"Successfully generated avatar URL for user {user_id}")
        except Exception as e:
            logger.exception(
                f"Unexpected error generating pre-signed URL for user {user_id},"
                f" key '{profile.avatar_url}': {e}"
            )

    profile_read = ProfileRead.model_validate(profile)
    profile_read.avatar_url = avatar_url

    logger.info(f"Retrieved profile for user_id: {user_id}")
    return profile_read


@router.put(
    "/me",
    response_model=ProfileRead,
    summary="Create or update current user's profile",
    description=(
        "Creates a profile if one doesn't exist for the authenticated user, "
        "or updates the existing one. Uses PUT for idempotency."
    ),
)
async def create_or_update_my_profile(  # noqa: PLR0912, PLR0913, PLR0915 : TODO: Divide this func or find another solution to fix an error
    request: Request,
    user_id: CurrentUserUUID,
    session: AsyncSession = Depends(get_async_session),
    display_name: Annotated[str | None, Form()] = None,
    bio: Annotated[str | None, Form()] = None,
    icon: Annotated[UploadFile | None, File()] = None,
):
    """Creates or updates the profile for the user identified by the JWT."""
    try:
        s3: S3Client = request.app.state.s3_client
    except AttributeError:
        logger.error("S3Client not found in application state. Check lifespan initialization.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 storage service is not configured correctly.",
        )
    object_key: str | None = None

    if icon:
        try:
            contents = await icon.read()

            file_uuid, extension = await s3.upload_file(
                file_content=contents,
                content_type=icon.content_type,
                prefix=USER_ICON_PREFIX,
                original_filename=icon.filename,
            )

            object_key = f"{USER_ICON_PREFIX}{file_uuid}{extension}"
        except Exception as e:
            logger.error(f"Avatar upload failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not determine file type for upload: {e}",
            )
        finally:
            if icon:
                await icon.close()

    profile_data_to_update = {
        "display_name": display_name,
        "bio": bio,
    }

    if object_key:
        profile_data_to_update["avatar_url"] = object_key

    update_data_filtered = {k: v for k, v in profile_data_to_update.items() if v is not None}

    # Try to fetch existing profile
    try:
        statement = select(Profile).where(Profile.user_id == user_id)
        result = await session.execute(statement)
        db_profile = result.scalar_one_or_none()

        if db_profile:
            # Update existing profile
            logger.info(f"Updating profile for user_id: {user_id}")
            for key, value in update_data_filtered.items():
                setattr(db_profile, key, value)
            session.add(db_profile)
            profile_to_return = db_profile
        else:
            # Create new profile
            logger.info(f"Creating new profile for user_id: {user_id}")
            create_data = update_data_filtered
            create_data["user_id"] = user_id
            db_profile = Profile(**create_data)
            session.add(db_profile)
            profile_to_return = db_profile

        await session.commit()
        await session.refresh(profile_to_return)
        logger.info(f"Successfully committed profile changes for user_id: {user_id}")
    except IntegrityError:
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

    avatar_url: str | None = None
    if profile_to_return.avatar_url:
        try:
            avatar_url = await s3.get_file_url(
                object_key=profile_to_return.avatar_url, expires_in=ICON_URL_EXPIRY_SECONDS
            )
        except Exception as e:
            logger.error(
                f"Failed to generate pre-signed URL for response after PUT for user {user_id}: {e}",
                exc_info=True,
            )

    response_data = ProfileRead.model_validate(profile_to_return).model_dump()
    response_data["avatar_url"] = avatar_url

    logger.info(f"Profile update/create successful for user_id: {user_id}. Returning profile.")
    return response_data
