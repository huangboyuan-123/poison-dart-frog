"""
Schema 路由 — 获取数据库表结构信息。
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..agent import SQLAgent
from ..models import SchemaResponse

router = APIRouter(prefix="/api", tags=["schema"])

# 复用 query 模块的 agent 单例（同一进程共享）
_agent: Optional[SQLAgent] = None


def get_agent() -> SQLAgent:
    """获取或创建 Agent 单例。"""
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent


@router.get("/schema", response_model=SchemaResponse)
async def get_full_schema():
    """
    获取数据库所有表的完整结构。

    返回每个表的列名、类型、是否可空、键信息等。
    """
    agent = get_agent()
    try:
        schema = agent.db.get_schema()
        db_name = agent.db.engine.url.database if agent.db.engine.url else "unknown"
        return SchemaResponse(database=db_name, tables=schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Schema 失败: {e}")


@router.get("/schema/{table_name}")
async def get_table_schema(table_name: str):
    """
    获取指定表的详细结构。

    Args:
        table_name: 表名（URL 路径参数）
    """
    agent = get_agent()
    info = agent.db.get_table_info(table_name)

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"表 '{table_name}' 不存在",
        )

    return {"table": info["table"], "columns": info["columns"]}
