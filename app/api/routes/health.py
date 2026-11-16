import time
from fastapi import APIRouter
from sqlalchemy import text
from app.config import settings
from app.database.session import db_manager
from app.services.cache import cache

router = APIRouter(tags=["Health"])

START_TIME = time.time()


@router.get("/health")
async def health_check():
    """System health check endpoint verifying database, cache, and bot status."""
    uptime_seconds = int(time.time() - START_TIME)

    # Check database connectivity
    db_healthy = False
    try:
        async with db_manager.session_maker() as session:
            await session.execute(text("SELECT 1"))
            db_healthy = True
    except Exception:
        db_healthy = False

    return {
        "status": "ok" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "error",
        "cache": cache.status_str,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "webhook_url": settings.full_webhook_url,
    }
