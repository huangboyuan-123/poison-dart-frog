"""
表操作路由 — 表结构设计、行增删改。
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agent import SQLAgent

router = APIRouter(prefix="/api/table", tags=["table"])

_agent: Optional[SQLAgent] = None


def get_agent() -> SQLAgent:
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent


class UpdateRowRequest(BaseModel):
    database: str = Field(..., description="数据库名")
    table: str = Field(..., description="表名")
    pk_column: str = Field(..., description="主键列名")
    pk_value: str = Field(..., description="主键值")
    column: str = Field(..., description="要更新的列名")
    value: str = Field(..., description="新值")


class InsertRowRequest(BaseModel):
    database: str = Field(..., description="数据库名")
    table: str = Field(..., description="表名")
    values: dict = Field(..., description="列名→值的映射")


class DeleteRowRequest(BaseModel):
    database: str = Field(..., description="数据库名")
    table: str = Field(..., description="表名")
    pk_column: str = Field(..., description="主键列名")
    pk_value: str = Field(..., description="主键值")


@router.post("/update")
async def update_row(req: UpdateRowRequest):
    """更新表的一行数据。"""
    agent = get_agent()
    # 空值/NULL 处理 + 单引号转义
    if not req.value or req.value.upper() == 'NULL':
        val_sql = "NULL"
    else:
        escaped = req.value.replace("\\", "\\\\").replace("'", "\\'")
        val_sql = f"'{escaped}'"
    escaped_pk = req.pk_value.replace("\\", "\\\\").replace("'", "\\'")
    sql = (
        f"UPDATE `{req.database}`.`{req.table}` "
        f"SET `{req.column}` = {val_sql} "
        f"WHERE `{req.pk_column}` = '{escaped_pk}'"
    )
    result = agent.db.execute_sql(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "affected": result["data"]["row_count"] if result["data"] else 0}


@router.post("/insert")
async def insert_row(req: InsertRowRequest):
    """插入一行数据。"""
    agent = get_agent()
    cols = ", ".join(f"`{k}`" for k in req.values)
    vals_parts = []
    for v in req.values.values():
        if not v or str(v).upper() == 'NULL':
            vals_parts.append("NULL")
        else:
            escaped = str(v).replace("\\", "\\\\").replace("'", "\\'")
            vals_parts.append(f"'{escaped}'")
    vals = ", ".join(vals_parts)
    sql = f"INSERT INTO `{req.database}`.`{req.table}` ({cols}) VALUES ({vals})"
    result = agent.db.execute_sql(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "affected": result["data"]["row_count"] if result["data"] else 1}


@router.post("/delete")
async def delete_row(req: DeleteRowRequest):
    """删除一行数据。"""
    agent = get_agent()
    sql = (
        f"DELETE FROM `{req.database}`.`{req.table}` "
        f"WHERE `{req.pk_column}` = '{req.pk_value}'"
    )
    result = agent.db.execute_sql(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "affected": result["data"]["row_count"] if result["data"] else 1}


@router.get("/ddl")
async def get_table_ddl(database: str, table: str):
    """获取建表 DDL。"""
    agent = get_agent()
    try:
        with agent.db.engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text(f"SHOW CREATE TABLE `{database}`.`{table}`"))
            row = result.fetchone()
            if row:
                return {"table": row[0], "ddl": row[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail=f"表 {database}.{table} 不存在")
