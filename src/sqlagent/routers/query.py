"""
查询路由 — 自然语言转 SQL 并执行。
"""

import re
from typing import Any

from fastapi import APIRouter

from ..agent import SQLAgent
from ..models import ExecuteRequest, ExecuteResponse, QueryRequest, QueryResponse

router = APIRouter(prefix="/api", tags=["query"])

# 全局 Agent 单例（模块加载时创建）
_agent: SQLAgent | None = None


def get_agent() -> SQLAgent:
    """获取或创建 Agent 单例。"""
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent


def _extract_sql(output: str) -> str | None:
    """
    从 Agent 输出中提取 SQL 语句。

    尝试匹配 ```sql ... ``` 代码块或 SELECT 开头的语句。
    """
    # 匹配 ```sql ... ``` 代码块
    sql_block = re.search(r"```sql\s*(.*?)```", output, re.DOTALL | re.IGNORECASE)
    if sql_block:
        return sql_block.group(1).strip()

    # 匹配 SELECT 开头的语句（直到分号或换行符 + 非空格）
    select_match = re.search(
        r"(SELECT\s+.*?;)", output, re.DOTALL | re.IGNORECASE
    )
    if select_match:
        return select_match.group(1).strip()

    return None


@router.post("/query", response_model=QueryResponse)
async def natural_language_query(req: QueryRequest):
    """
    自然语言查询接口。

    将用户的问题转换为 SQL 并执行，返回结构化的查询结果和 AI 分析。

    示例请求:
    ```json
    {"question": "查询数据库中所有表"}
    ```
    """
    agent = get_agent()
    result = agent.run(req.question)

    if not result.get("success"):
        return QueryResponse(
            success=False,
            question=req.question,
            error=result.get("error", "未知错误"),
        )

    output = result.get("output", "")
    sql = _extract_sql(output)

    return QueryResponse(
        success=True,
        question=req.question,
        sql=sql,
        answer=output,
    )


@router.post("/execute", response_model=ExecuteResponse)
async def execute_sql(req: ExecuteRequest):
    """
    直接执行 SQL 语句。

    默认只读模式，需要写操作时设置 read_only=false。

    示例请求:
    ```json
    {"sql": "SELECT * FROM users LIMIT 5", "read_only": true}
    ```
    """
    agent = get_agent()
    result = agent.db.execute_sql(req.sql, read_only=req.read_only)

    return ExecuteResponse(
        success=result["success"],
        sql=req.sql,
        data=result.get("data"),
        error=result.get("error"),
    )


@router.get("/history", response_model=dict[str, Any])
async def query_history():
    """
    查询历史记录（当前会话）。

    注意: 当前版本使用内存存储，重启后清空。
    """
    agent = get_agent()
    memory = agent._executor.memory

    if not memory or not hasattr(memory, "chat_memory"):
        return {"total": 0, "items": []}

    messages = memory.chat_memory.messages
    items = [
        {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
        for msg in messages
    ]

    return {"total": len(items), "items": items}
