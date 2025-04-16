import asyncio
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from auth_lib.auth import get_current_user_id
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.api.endpoints import router
from app.core.database import get_async_session

logger = logging.getLogger(__name__)

TEST_USER_ID = uuid.uuid4()

TEST_POSTGRES_SERVER=os.environ.get("TEST_DATABASE_URL", "localhost")
TEST_POSTGRES_PORT=os.environ.get("TEST_DATABASE_URL", "5432")
TEST_POSTGRES_USER=os.environ.get("TEST_DATABASE_URL", "postgres")
TEST_POSTGRES_PASSWORD=os.environ.get("TEST_DATABASE_URL", "postgres")
TEST_POSTGRES_DB=os.environ.get("TEST_DATABASE_URL", "test_profile_db")

TEST_DATABASE_URL = f"postgresql+asyncpg://{TEST_POSTGRES_USER}:{TEST_POSTGRES_PASSWORD}@{TEST_POSTGRES_SERVER}:{TEST_POSTGRES_PORT}/{TEST_POSTGRES_DB}"
# TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_profile_db"

test_async_engine = create_async_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=True,
    future=True,
    poolclass=NullPool,
)

TestingAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


@pytest_asyncio.fixture(scope="session")
async def get_test_async_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency for async session."""
    logger.debug("Creating test async session")
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
            logger.debug("Test session yielded")
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Test session closed")


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_app():
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        logger.info("Test application startup...")
        async with test_async_engine.connect() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Test database connection successful during startup.")

        yield

        logger.info("Test application shutdown...")
        await test_async_engine.dispose()
        logger.info("Database engine disposed.")

    app = FastAPI(
        lifespan=test_lifespan
    )
    app.include_router(router)
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    app.dependency_overrides[get_async_session] = override_get_async_session

    async with LifespanManager(app) as manager:
        logger.info("We're in!")
        yield manager.app


@pytest_asyncio.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        logger.info("Client usage finished.")


@pytest_asyncio.fixture
async def test_user_id():
    return TEST_USER_ID
