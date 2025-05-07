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
    Should return a default profile if none exists (see endpoints.py logic).
    """
    # when...
    response = await client.get("/me")
    data = response.json()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert data["user_id"]
    assert data["display_name"] is None
    assert data["bio"] is None


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
async def test_update_profile_with_icon(
    client: AsyncClient, test_user_id: CurrentUserUUID, test_session: AsyncSession
):
    # given...
    unique_username = str(uuid.uuid4())
    unique_bio = str(uuid.uuid4())
    unique_icon_content = bytes(str(uuid.uuid4()), "utf-8")
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
    unique_icon_content = bytes(str(uuid.uuid4()), "utf-8")
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


@pytest.mark.asyncio
async def test_get_profile_by_id(client: AsyncClient, test_user_id: uuid.UUID, test_session: AsyncSession):
    # given...
    profile = Profile(user_id=test_user_id, display_name="User", bio="Bio")
    test_session.add(profile)
    await test_session.commit()
    await test_session.refresh(profile)

    # when...
    response = await client.get(f"/profile/{test_user_id}")
    data = response.json()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert data["user_id"] == str(test_user_id)
    assert data["display_name"] == "User"
    assert data["bio"] == "Bio"


@pytest.mark.asyncio
async def test_get_profile_by_id_not_found(client: AsyncClient):
    # given...
    random_id = str(uuid.uuid4())

    # when...
    response = await client.get(f"/profile/{random_id}")

    # then...
    assert response.status_code == status.HTTP_404_NOT_FOUND
