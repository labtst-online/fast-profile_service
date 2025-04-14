import uuid

import pytest
from fastapi import Depends, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate

from .conftest import TEST_USER_ID, get_async_session


async def test_get_my_profile_not_found(client: AsyncClient):
    """
    Check profile not found if this one does not exist in the database
    """
    # when...
    response = await client.get("/me")

    # then...
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Profile not found"}


async def test_get_my_profile_found(
    client: AsyncClient,
    session: AsyncSession = Depends(get_async_session)):
    """
    Check profile found if this one exist in the database
    """
    # given...
    unique_username = str(uuid.uuid4)
    unique_bio = str(uuid.uuid4)
    existing_profile = Profile(
        user_id=TEST_USER_ID,
        display_name=unique_username,
        bio=unique_bio
    )
    session.add(existing_profile)
    await session.commit()
    await session.refresh(existing_profile)

    # when...
    response = await client.get("/me")
    response_data = response.json()

    # then...
    assert response.status_code == status.HTTP_200_OK
    assert response_data["user_id"] == str(TEST_USER_ID)
    assert response_data["display_name"] == unique_username
    assert response_data["bio"] == unique_bio
