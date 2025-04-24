import uuid
from io import BytesIO

import pytest
from auth_lib.auth import CurrentUserUUID
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.profile import Profile


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
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    """
    Check profile found if this one exist in the database
    """
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    existing_profile = Profile(user_id=test_user_id, display_name=unique_username, bio=unique_bio)
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
async def test_create_profile_without_icon(
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    profile_form_data = {
        "display_name": unique_username,
        "bio": unique_bio,
    }

    # when...
    response = await client.put("/me", data=profile_form_data, files={})
    response_data = response.json()
    result = await test_session.execute(select(Profile).where(Profile.user_id == test_user_id))
    created_profile = result.scalar_one_or_none()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == unique_username
    assert response_data["bio"] == unique_bio
    assert response_data["avatar_url"] is None
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert created_profile is not None
    assert created_profile.user_id == test_user_id


@pytest.mark.asyncio
async def test_update_profile_without_icon(
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    existing_profile = Profile(user_id=test_user_id, display_name=unique_username, bio=unique_bio)
    test_session.add(existing_profile)
    await test_session.commit()
    await test_session.refresh(existing_profile)

    unique_username_for_update = str(uuid.uuid4())
    unique_bio_for_update = str(uuid.uuid4())
    profile_form_data_for_update = {
        "display_name": unique_username_for_update,
        "bio": unique_bio_for_update,
    }

    # when...
    response = await client.put("/me", data=profile_form_data_for_update, files={})
    response_data = response.json()
    result = await test_session.execute(select(Profile).where(Profile.user_id == test_user_id))
    updated_profile = result.scalar_one_or_none()

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
async def test_update_profile_partially_without_icon(
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    existing_profile = Profile(user_id=test_user_id, display_name=unique_username, bio=unique_bio)
    test_session.add(existing_profile)
    await test_session.commit()
    await test_session.refresh(existing_profile)

    unique_bio_for_update = str(uuid.uuid4())
    profile_form_data_for_update = {
        "bio": unique_bio_for_update,
    }

    # when...
    response = await client.put("/me", data=profile_form_data_for_update, files={})
    response_data = response.json()
    result = await test_session.execute(select(Profile).where(Profile.user_id == test_user_id))
    updated_profile = result.scalar_one_or_none()

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


@pytest.mark.asyncio
async def test_create_profile_with_icon(
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    unique_icon_content = bytes(str(uuid.uuid4()), 'utf-8')
    profile_form_data = {
        "display_name": unique_username,
        "bio": unique_bio,
    }
    icon_file_data = {"icon": ("test_icon.png", BytesIO(unique_icon_content), "image/png")}
    # when...
    response = await client.put("/me", data=profile_form_data, files=icon_file_data)
    response_data = response.json()
    result = await test_session.execute(select(Profile).where(Profile.user_id == test_user_id))
    created_profile = result.scalar_one_or_none()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == unique_username
    assert response_data["bio"] == unique_bio
    assert response_data.get("avatar_url") is not None
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert created_profile is not None
    assert created_profile.user_id == test_user_id


@pytest.mark.asyncio
async def test_update_profile_with_icon(
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    unique_icon_content = bytes(str(uuid.uuid4()), 'utf-8')
    existing_profile = Profile(user_id=test_user_id, display_name=unique_username, bio=unique_bio)
    test_session.add(existing_profile)
    await test_session.commit()
    await test_session.refresh(existing_profile)

    unique_username_for_update = str(uuid.uuid4())
    unique_bio_for_update = str(uuid.uuid4())
    profile_form_data_for_update = {
        "display_name": unique_username_for_update,
        "bio": unique_bio_for_update,
    }
    icon_file_data = {"icon": ("test_icon.png", BytesIO(unique_icon_content), "image/png")}

    # when...
    response = await client.put("/me", data=profile_form_data_for_update, files=icon_file_data)
    response_data = response.json()
    result = await test_session.execute(select(Profile).where(Profile.user_id == test_user_id))
    updated_profile = result.scalar_one_or_none()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == unique_username_for_update
    assert response_data["bio"] == unique_bio_for_update
    assert response_data["avatar_url"] is not None
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
async def test_update_profile_partially_with_icon(
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    unique_icon_content = bytes(str(uuid.uuid4()), 'utf-8')
    existing_profile = Profile(user_id=test_user_id, display_name=unique_username, bio=unique_bio)
    test_session.add(existing_profile)
    await test_session.commit()
    await test_session.refresh(existing_profile)

    unique_bio_for_update = str(uuid.uuid4())
    profile_form_data_for_update = {
        "bio": unique_bio_for_update,
    }
    icon_file_data = {"icon": ("test_icon.png", BytesIO(unique_icon_content), "image/png")}
    # when...
    response = await client.put("/me", data=profile_form_data_for_update, files=icon_file_data)
    response_data = response.json()
    result = await test_session.execute(select(Profile).where(Profile.user_id == test_user_id))
    updated_profile = result.scalar_one_or_none()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["display_name"] == existing_profile.display_name
    assert response_data["bio"] == unique_bio_for_update
    assert response_data["avatar_url"] is not None
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
