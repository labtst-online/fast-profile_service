import asyncio
import logging
import os
import uuid
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from auth_lib import CurrentUserUUID
from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from app.core.database import get_async_session
from app.main import app

# from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

TEST_POSTGRES_SERVER=os.environ.get("TEST_DATABASE_URL", "localhost")
TEST_POSTGRES_PORT=os.environ.get("TEST_DATABASE_URL", "5432")
TEST_POSTGRES_USER=os.environ.get("TEST_DATABASE_URL", "postgres")
TEST_POSTGRES_PASSWORD=os.environ.get("TEST_DATABASE_URL", "postgres")
TEST_POSTGRES_DB=os.environ.get("TEST_DATABASE_URL", "test_profile_db")

TEST_DATABASE_URL = f"postgresql+asyncpg://{TEST_POSTGRES_USER}:{TEST_POSTGRES_PASSWORD}@{TEST_POSTGRES_SERVER}:{TEST_POSTGRES_PORT}/{TEST_POSTGRES_DB}"

if not TEST_DATABASE_URL:
    logger.error("TEST DATABASE not set" )
    raise RuntimeError

engine = create_async_engine(TEST_DATABASE_URL, )  ##poolclass=NullPool

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """ Стандартная фикстура для pytest-asyncio """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with TestingSessionLocal() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


TEST_USER_ID = uuid.uuid4()


async def override_get_current_user_id() -> uuid.UUID:
    return TEST_USER_ID


async def override_get_async_session(
    session: AsyncSession = Depends(db_session)
) -> AsyncGenerator[AsyncSession]:
    yield session


app.dependency_overrides[get_async_session] = override_get_async_session
app.dependency_overrides[CurrentUserUUID] = override_get_current_user_id


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        yield async_client
