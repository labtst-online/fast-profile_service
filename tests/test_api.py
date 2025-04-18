import uuid

import pytest
from auth_lib.auth import CurrentUserUUID
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate


@pytest.mark.asyncio
async def test_get_my_profile_not_found(client: AsyncClient):
    """
    Check profile not found if this one does not exist in the database
    """
    # when...
    response = await client.get("/me")

    # then...
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Profile not found"}


@pytest.mark.asyncio
async def test_get_my_profile_found(
    client: AsyncClient,
    test_user_id: CurrentUserUUID,
    test_session: AsyncSession
):
    """
    Check profile found if this one exist in the database
    """
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    existing_profile = Profile(
        user_id=test_user_id,
        display_name=unique_username,
        bio=unique_bio
    )
    test_session.add(existing_profile)
    await test_session.commit()
    await test_session.refresh(existing_profile)

    # when...
    response = await client.get("/me")
    response_data = response.json()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == unique_username
    assert response_data["bio"] == unique_bio


@pytest.mark.asyncio
async def test_create_profile(
    client: AsyncClient,
    test_user_id: CurrentUserUUID,
    test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    unique_avatar_url = str(uuid.uuid4())
    profile_data = ProfileUpdate(
        display_name=unique_username,
        bio=unique_bio,
        avatar_url=unique_avatar_url
    )

    # when...
    response = await client.put("/me", json=profile_data.model_dump())
    response_data = response.json()
    result = await test_session.execute(
        select(Profile).where(Profile.user_id == test_user_id)
    )
    created_profile = result.scalars().first()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == unique_username
    assert response_data["bio"] == unique_bio
    assert response_data["avatar_url"] == unique_avatar_url
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert created_profile is not None
    assert created_profile.user_id == test_user_id


@pytest.mark.asyncio
async def test_update_profile(
    client: AsyncClient,
    test_user_id: CurrentUserUUID,
    test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    existing_profile = Profile(
        user_id=test_user_id,
        display_name=unique_username,
        bio=unique_bio
    )
    test_session.add(existing_profile)
    await test_session.commit()
    await test_session.refresh(existing_profile)

    unique_username_for_update = str(uuid.uuid4())
    unique_bio_for_update = str(uuid.uuid4())
    profile_data_for_update = ProfileUpdate(
        display_name=unique_username_for_update,
        bio=unique_bio_for_update
    )

    # when...
    response = await client.put("/me", json=profile_data_for_update.model_dump())
    response_data = response.json()
    result = await test_session.execute(
        select(Profile).where(Profile.user_id == test_user_id)
    )
    updated_profile = result.scalars().first()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == unique_username_for_update
    assert response_data["bio"] == unique_bio_for_update
    assert response_data["id"] == str(existing_profile.id)
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert response_data["created_at"] == existing_profile.created_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert response_data["updated_at"] != existing_profile.updated_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert response_data["created_at"] != response_data["updated_at"]
    assert updated_profile is not None
    assert updated_profile.user_id == test_user_id


@pytest.mark.asyncio
async def test_update_profile_partially(
    client: AsyncClient,
    test_user_id: CurrentUserUUID,
    test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    existing_profile = Profile(
        user_id=test_user_id,
        display_name=unique_username,
        bio=unique_bio
    )
    test_session.add(existing_profile)
    await test_session.commit()
    await test_session.refresh(existing_profile)

    unique_bio_for_update = str(uuid.uuid4())
    profile_data_for_update = ProfileUpdate(bio=unique_bio_for_update)

    # when...
    response = await client.put("/me", json=profile_data_for_update.model_dump())
    response_data = response.json()
    result = await test_session.execute(
        select(Profile).where(Profile.user_id == test_user_id)
    )
    updated_profile = result.scalars().first()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == existing_profile.display_name
    assert response_data["bio"] == unique_bio_for_update
    assert response_data["id"] == str(existing_profile.id)
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert response_data["created_at"] == existing_profile.created_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert response_data["updated_at"] != existing_profile.updated_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert response_data["created_at"] != response_data["updated_at"]
    assert updated_profile is not None
    assert updated_profile.user_id == test_user_id
