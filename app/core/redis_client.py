import logging

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


async def get_redis_client(request: Request):
    if not hasattr(request.app.state, "redis_client") or request.app.state.redis_client is None:
        logger.error("Redis client not found in application state.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Redis service is not available.",
        )
    return request.app.state.redis_client
