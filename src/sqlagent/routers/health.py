"""
健康检查路由 — 返回数据库和 LLM 连接状态。
"""

from fastapi import APIRouter

from .. import __version__
from ..models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口。

    返回数据库连接和 LLM 连接的状态。
    可用于 Docker healthcheck 和监控系统。
    """
    from ..agent import SQLAgent

    agent = SQLAgent()
    result = agent.test_connections()

    return HealthResponse(
        status=result["status"],
        database=result["database"],
        llm=result["llm"],
        version=__version__,
    )
