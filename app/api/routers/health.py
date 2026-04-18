from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    # check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # check redis
    try:
        from app.core.config import settings
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    overall = (
        "healthy"
        if db_status == "healthy" and redis_status == "healthy"
        else "degraded"
    )

    return {
        "status": overall,
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
        },
    }