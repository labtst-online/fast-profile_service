import logging
import uuid
from typing import Annotated

import redis.asyncio as aioredis
from auth_lib.auth import CurrentUserUUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_session
from app.core.redis_client import get_redis_client
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
async def get_my_profile(  # noqa: PLR0915
    request: Request,
    user_id: CurrentUserUUID,
    session: AsyncSession = Depends(get_async_session),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    """Fetches the profile for the user identified by the JWT, including avatar URL from S3."""
    cache_key = f"profile:me:{user_id}"
    cache_ttl_seconds = 60

    try:
        cached_profile = await redis.get(cache_key)
        if cached_profile:
            logger.info(f"Cache HIT for user_id: {user_id}")
            profile_data = ProfileRead.model_validate_json(cached_profile)
            return profile_data
    except aioredis.RedisError as e:
        logger.error(f"Redis error: {e}")
    except Exception as e:
        logger.error(f"Error processing cached data for key '{cache_key}': {e}. Fetching from DB.")

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
        logger.info(f"Profile not found for user_id: {user_id}. Creating a default profile.")
        try:
            profile = Profile(user_id=user_id)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            logger.info(f"Successfully created default profile for user_id: {user_id}")
        except IntegrityError:
            await session.rollback()
            logger.error(f"Integrity error trying to create default profile for user_id: {user_id}")
            result = await session.execute(statement)
            profile = result.scalar_one_or_none()
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not create default profile.",
                )
        except Exception as e:
            await session.rollback()
            logger.exception(f"Error creating default profile for user_id: {user_id} - {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create default profile.",
            )

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

    try:
        profile_json_to_cache = profile_read.model_dump_json()
        await redis.set(cache_key, profile_json_to_cache, ex=cache_ttl_seconds)
        logger.info(f"Stored profile in cache for user_id: {user_id} with TTL {cache_ttl_seconds}s")
    except aioredis.RedisError as e:
        logger.error(
            f"Redis SET error for key '{cache_key}': {e}. Response served without caching."
        )
    except Exception as e:
        logger.error(f"Error serializing profile data for caching key '{cache_key}': {e}")

    logger.info(f"Retrieved profile for user_id: {user_id}")
    return profile_read


@router.put(
    "/me",
    response_model=ProfileRead,
    summary="Create or update current user's profile",
    description=("Updates the existing profile for the authenticated user."),
)
async def create_or_update_my_profile(  # noqa: PLR0912, PLR0913, PLR0915 : TODO: Divide this func or find another solution to fix troubles
    request: Request,
    user_id: CurrentUserUUID,
    session: AsyncSession = Depends(get_async_session),
    redis: aioredis.Redis = Depends(get_redis_client),
    display_name: Annotated[str | None, Form()] = None,
    bio: Annotated[str | None, Form()] = None,
    icon: Annotated[UploadFile | None, File()] = None,
):
    """Updates the profile for the user identified by the JWT."""
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

    if not update_data_filtered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided.",
        )

    # Fetch existing profile
    try:
        statement = select(Profile).where(Profile.user_id == user_id)
        result = await session.execute(statement)
        db_profile = result.scalar_one_or_none()

        if not db_profile:
            logger.error(f"Attempted to update non-existent profile for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Cannot update.",
            )

        # Update existing profile
        logger.info(f"Updating profile for user_id: {user_id}")
        for key, value in update_data_filtered.items():
            setattr(db_profile, key, value)
        session.add(db_profile)
        profile_to_return = db_profile

        await session.commit()
        await session.refresh(profile_to_return)
        logger.info(f"Successfully committed profile update for user_id: {user_id}")

        # Invalidate cache after successful update
        cache_key = f"profile:me:{user_id}"
        try:
            deleted_count = await redis.delete(cache_key)
            if deleted_count > 0:
                logger.info(f"Successfully invalidated cache for key: {cache_key}")
            else:
                logger.info(
                    f"Cache key not found or already expired during"
                    f" invalidation attempt: {cache_key}"
                )
        except aioredis.RedisError as e:
            logger.error(f"Redis cache invalidation error for key '{cache_key}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error during cache invalidation for key '{cache_key}': {e}")

    except IntegrityError:
        await session.rollback()
        logger.error(f"Integrity error during profile update for user_id: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Data conflict during profile update.",
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error updating profile for user_id: {user_id} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update profile.",
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

    logger.info(f"Profile update successful for user_id: {user_id}. Returning updated profile.")
    return response_data


@router.get(
    "/profile/{user_id}",
    response_model=ProfileRead,
    summary="Get a single profile",
    description="Retrieves the profile",
)
async def get_user_profile(
    request: Request,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    """Fetches the profile"""
    cache_key = f"profile:user:{user_id}"
    cache_ttl_seconds = 60

    try:
        cached_profile = await redis.get(cache_key)
        if cached_profile:
            logger.info(f"Cache HIT for profile_id: {user_id}")
            profile_data = ProfileRead.model_validate_json(cached_profile)
            return profile_data
    except aioredis.RedisError as e:
        logger.error(f"Redis error: {e}")
    except Exception as e:
        logger.error(f"Error processing cached data for key '{cache_key}': {e}. Fetching from DB.")

    try:
        s3: S3Client = request.app.state.s3_client
    except AttributeError:
        logger.error("S3Client not found in application state. Check lifespan initialization.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 storage service is not configured correctly.",
        )
    statement = select(Profile).where(Profile.user_id == user_id)
    result = await session.execute(statement)
    profile = result.scalar_one_or_none()

    if not profile:
        logger.info(f"Profile not found for post_id: {user_id}")
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

    try:
        profile_json_to_cache = profile_read.model_dump_json()
        await redis.set(cache_key, profile_json_to_cache, ex=cache_ttl_seconds)
        logger.info(
            f"Stored profile in cache for user_id: {user_id} with TTL {cache_ttl_seconds}s"
        )
    except aioredis.RedisError as e:
        logger.error(
            f"Redis SET error for key '{cache_key}': {e}. Response served without caching."
        )
    except Exception as e:
        logger.error(f"Error serializing profile data for caching key '{cache_key}': {e}")

    logger.info(f"Retrieved profile for user_id: {user_id}")
    return profile_read
