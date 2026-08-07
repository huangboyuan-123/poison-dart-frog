"""健康检查 — Redis 连接状态。"""
from fastapi import APIRouter
from .. import __version__
from ..models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        from .redis_routes import get_redis
        r = get_redis()
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return HealthResponse(status="healthy" if redis_ok else "unhealthy",
                          redis=redis_ok, version=__version__)
