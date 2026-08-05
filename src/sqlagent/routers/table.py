"""
表操作路由 — 表结构设计、行增删改（参数化查询防SQL注入）。
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text as sa_text

from ..agent import SQLAgent

router = APIRouter(prefix="/api/table", tags=["table"])

_agent: Optional[SQLAgent] = None


def get_agent() -> SQLAgent:
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent


class UpdateRowRequest(BaseModel):
    database: str
    table: str
    pk_column: str
    pk_value: str
    column: str
    value: str


class InsertRowRequest(BaseModel):
    database: str
    table: str
    values: dict


class DeleteRowRequest(BaseModel):
    database: str
    table: str
    pk_column: str
    pk_value: str


@router.post("/update")
async def update_row(req: UpdateRowRequest):
    """更新表的一行数据（参数化查询）。"""
    agent = get_agent()
    col_val = None if (not req.value or req.value.upper() == 'NULL') else req.value
    sql = sa_text(
        f"UPDATE `{req.database}`.`{req.table}` "
        f"SET `{req.column}` = :val "
        f"WHERE `{req.pk_column}` = :pk_val"
    ).bindparams(val=col_val, pk_val=req.pk_value)

    result = agent.db.execute_sql_raw(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "affected": result["data"]["row_count"] if result["data"] else 0}


@router.post("/insert")
async def insert_row(req: InsertRowRequest):
    """插入一行数据（参数化查询）。"""
    agent = get_agent()
    cols = list(req.values.keys())
    col_str = ", ".join(f"`{k}`" for k in cols)
    placeholders = ", ".join(f":{k}" for k in cols)

    # NULL → None for parameter binding
    params = {k: (None if not v or str(v).upper() == 'NULL' else v) for k, v in req.values.items()}

    sql = sa_text(
        f"INSERT INTO `{req.database}`.`{req.table}` ({col_str}) VALUES ({placeholders})"
    ).bindparams(**params)

    result = agent.db.execute_sql_raw(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "affected": result["data"]["row_count"] if result["data"] else 1}


@router.post("/delete")
async def delete_row(req: DeleteRowRequest):
    """删除一行数据（参数化查询）。"""
    agent = get_agent()
    sql = sa_text(
        f"DELETE FROM `{req.database}`.`{req.table}` "
        f"WHERE `{req.pk_column}` = :pk_val"
    ).bindparams(pk_val=req.pk_value)

    result = agent.db.execute_sql_raw(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "affected": result["data"]["row_count"] if result["data"] else 1}


@router.get("/ddl")
async def get_table_ddl(database: str, table: str):
    """获取建表 DDL（参数化查询）。"""
    agent = get_agent()
    try:
        with agent.db.engine.connect() as conn:
            sql = sa_text("SHOW CREATE TABLE :tbl").bindparams(
                tbl=f"`{database}`.`{table}`"
            )
            result = conn.execute(sa_text(
                f"SHOW CREATE TABLE `{database}`.`{table}`"
            ))
            row = result.fetchone()
            if row:
                return {"table": row[0], "ddl": row[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail=f"表 {database}.{table} 不存在")


@router.delete("/drop")
async def drop_table(database: str, table: str):
    """删除表 (DROP TABLE)"""
    agent = get_agent()
    sql = f"DROP TABLE `{database}`.`{table}`"
    result = agent.db.execute_sql(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "message": f"表 {database}.{table} 已删除"}


@router.delete("/database/drop")
async def drop_database(database: str):
    """删除数据库 (DROP DATABASE)"""
    agent = get_agent()
    sql = f"DROP DATABASE `{database}`"
    result = agent.db.execute_sql(sql, read_only=False)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "message": f"数据库 {database} 已删除"}
