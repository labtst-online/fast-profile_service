import logging

from auth_lib.auth import CurrentUserUUID
from core.s3_client import S3Client
from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_session
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

    avatar_url = None
    if profile.avatar_url:
        try:
            prefix, filename = profile.avatar_url.split('/')

            file_uuid, extension = filename.split('.', 1)
            extension = f".{extension}"

            avatar_url = await s3.get_file_url(
                file_uuid=file_uuid,
                extension=extension,
                prefix=prefix,
                expires_in=3600
            )
        except ValueError:
            logger.error(f"Invalid S3 path format in avatar_url: {profile.avatar_url}")
        except Exception as e:
            logger.error(f"Failed to generate avatar URL for user {user_id}: {e}")

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
async def create_or_update_my_profile(
    request: Request,
    user_id: CurrentUserUUID,
    session: AsyncSession = Depends(get_async_session),
    display_name: Form = None,
    bio: Form = None,
    icon: UploadFile = None,
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

    update_data = {"display_name": display_name, "bio": bio}
    avatar_data = {}

    # Process icon upload if present
    if icon:
        try:
            # Read file content first for safety checks
            contents = await icon.read()

            # Upload to S3 (client handles extension/type validation)
            file_uuid, extension = await s3.upload_file(
                file_content=contents,
                content_type=icon.content_type,
                prefix=USER_ICON_PREFIX,
                original_filename=icon.filename,
            )

            # Construct full S3 path from client response
            avatar_data["avatar_url"] = f"{USER_ICON_PREFIX}{file_uuid}{extension}"
        except Exception as e:
            logger.error(f"Avatar upload failed: {str(e)}")
            raise HTTPException(400, "Invalid image file") from e
        finally:
            await icon.close()

    update_data = {k: v for k, v in {**update_data, **avatar_data}.items() if v is not None}

    # Try to fetch existing profile
    try:
        statement = select(Profile).where(Profile.user_id == user_id)
        result = await session.execute(statement)
        db_profile = result.scalar_one_or_none()

        if db_profile:
            # Update existing profile
            logger.info(f"Updating profile for user_id: {user_id}")
            for key, value in update_data.items():
                if hasattr(db_profile, key):
                    setattr(db_profile, key, value)
                else:
                    logger.warning(
                        f"Model 'Profile' has no attribute '{key}'. Skipping update for this field."
                    )
            session.add(db_profile)
            profile_to_return = db_profile
        else:
            # Create new profile
            logger.info(f"Creating new profile for user_id: {user_id}")
            create_data = update_data
            create_data["user_id"] = user_id
            db_profile = Profile(**create_data, user_id=user_id)
            session.add(db_profile)

        await session.commit()
        await session.refresh(profile_to_return)
        logger.info(f"Successfully committed profile changes for user_id: {user_id}")
        return profile_to_return
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
