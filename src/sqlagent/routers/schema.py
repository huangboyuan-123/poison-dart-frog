"""
Schema 路由 — 获取数据库/表结构信息。
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..agent import SQLAgent
from ..models import SchemaResponse

router = APIRouter(prefix="/api", tags=["schema"])

_agent: Optional[SQLAgent] = None


def get_agent() -> SQLAgent:
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent


@router.get("/databases")
async def list_databases():
    """获取 MySQL 服务器上所有数据库列表。"""
    agent = get_agent()
    try:
        dbs = agent.db.get_databases()
        return {"databases": dbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema", response_model=SchemaResponse)
async def get_full_schema(database: Optional[str] = Query(None)):
    """获取指定数据库(或当前库)的所有表结构。"""
    agent = get_agent()
    try:
        schema = agent.db.get_schema(database)
        db_name = database or (agent.db.engine.url.database if agent.db.engine.url else "unknown")
        return SchemaResponse(database=db_name, tables=schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Schema 失败: {e}")


@router.get("/schema/{table_name}")
async def get_table_schema(table_name: str, database: Optional[str] = Query(None)):
    """获取指定表的详细结构。"""
    agent = get_agent()
    info = agent.db.get_table_info(table_name, database)

    if not info:
        raise HTTPException(status_code=404, detail=f"表 '{table_name}' 不存在")

    return {"table": info["table"], "columns": info["columns"]}
