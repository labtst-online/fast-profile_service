import logging
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile

from .api.routers.endpoints import router as profile_router
from .core.config import settings
from .core.database import async_engine, get_async_session
from .core.s3_client import S3Client

logging.basicConfig(level=logging.INFO if settings.APP_ENV == "production" else logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    __version__ = version("profile_service")
except PackageNotFoundError:
    __version__ = "0.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    # You can add startup logic here, like checking DB connection
    try:
        async with async_engine.connect():
            logger.info("Database connection successful during startup.")
    except Exception as e:
        logger.error(f"Database connection failed during startup: {e}")

    try:
        s3_client = S3Client(
            AWS_ACCESS_KEY_ID=settings.AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY=settings.AWS_SECRET_ACCESS_KEY,
            BUCKET_NAME=settings.AWS_S3_BUCKET_NAME,
            REGION_NAME=settings.AWS_S3_REGION,
        )
        app.state.s3_client = s3_client
        logger.info("S3 Client initialized successfully.")
    except Exception as e:
        logger.error(f"S3 Client initialization failed during startup: {e}")
        raise RuntimeError()

    try:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}"
        redis_client = aioredis.from_url(redis_url)
        await redis_client.ping()
        app.state.redis_client = redis_client
        logger.info(f"Redis client connected successfully to {redis_url}")
    except Exception as e:
        logger.error(f"Redis connection failed during startup: {e}")
        app.state.redis_client = None

    yield

    logger.info("Application shutdown...")
    await redis_client.close()
    await async_engine.dispose()
    logger.info("Database engine disposed.")


app = FastAPI(
    title="Profile Service",
    description="Handles user profiles.",
    version=__version__,
    lifespan=lifespan,
)


app.include_router(profile_router, prefix="/profiles", tags=["Profiles"])


@app.get("/test-db/", summary="Test Database Connection", tags=["Test"])
async def test_db_connection(session: AsyncSession = Depends(get_async_session)):
    """
    Attempts to retrieve the first profile from the database.
    """
    logger.info("Accessing /test-db/ endpoint")
    try:
        statement = select(Profile).limit(1)
        result = await session.execute(statement)
        profile = result.scalar_one_or_none()

        if profile:
            logger.info(f"Successfully retrieved profile: {profile.id}")
            return {"status": "success", "first_user_profile": profile.id}
        else:
            logger.info("No profile found in the database.")
            return {"status": "success", "message": "No profile found"}
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/", summary="Health Check", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "Profile Service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=(settings.APP_ENV == "development"),
        log_level="info",
    )
