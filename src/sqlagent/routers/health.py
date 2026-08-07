"""
健康检查路由 — 返回数据库和 LLM 连接状态。
"""

from typing import Optional

from fastapi import APIRouter

from .. import __version__
from ..agent import SQLAgent
from ..models import HealthResponse

router = APIRouter(tags=["health"])

_health_agent: Optional[SQLAgent] = None


def get_health_agent() -> SQLAgent:
    global _health_agent
    if _health_agent is None:
        _health_agent = SQLAgent()
    return _health_agent


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口。复用 Agent 单例，避免每次创建新连接池。
    """
    agent = get_health_agent()
    result = agent.test_connections()

    return HealthResponse(
        status=result["status"],
        database=result["database"],
        llm=result["llm"],
        version=__version__,
    )
