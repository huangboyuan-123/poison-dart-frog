"""
查询路由 — 自然语言转 SQL 并执行。
"""

import re
from typing import Any, Dict, Optional

from fastapi import APIRouter

from ..agent import SQLAgent
from ..models import ExecuteRequest, ExecuteResponse, QueryRequest, QueryResponse

router = APIRouter(prefix="/api", tags=["query"])

# 两套 Agent：生成 SQL 用（不执行），执行 SQL 用
_query_agent: Optional[SQLAgent] = None
_exec_agent: Optional[SQLAgent] = None


def get_query_agent() -> SQLAgent:
    """获取生成 SQL 的 Agent（只有 schema 工具，不能执行 SQL）。"""
    global _query_agent
    if _query_agent is None:
        _query_agent = SQLAgent(execute_enabled=False)
    return _query_agent


def get_exec_agent() -> SQLAgent:
    """获取执行 SQL 的 Agent（完整工具集）。"""
    global _exec_agent
    if _exec_agent is None:
        _exec_agent = SQLAgent()
    return _exec_agent


def _extract_sql(output: str) -> Optional[str]:
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
    agent = get_query_agent()   # ← 只有 schema 工具，不能执行 SQL
    result = agent.run(req.question)

    if not result.get("success"):
        return QueryResponse(
            success=False,
            question=req.question,
            error=result.get("error", "未知错误"),
        )

    output = result.get("output", "")
    sql = _extract_sql(output)

    # 如果输出中没有提取到 SQL，尝试从 Agent 的中间步骤中提取
    if not sql:
        for step in result.get("intermediate_steps", []):
            # step 是 (action, observation) 元组
            action = step[0] if step else None
            if action and hasattr(action, 'tool_input'):
                tool_input = action.tool_input
                if isinstance(tool_input, dict) and 'sql' in tool_input:
                    sql = tool_input['sql']
                    break
                elif isinstance(tool_input, str):
                    # 检查是否是有效的 SQL
                    if re.match(r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|SHOW|DESCRIBE|EXPLAIN)\b',
                                tool_input, re.I):
                        sql = tool_input
                        break

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
    agent = get_exec_agent()
    result = agent.db.execute_sql(req.sql, read_only=req.read_only)

    return ExecuteResponse(
        success=result["success"],
        sql=req.sql,
        data=result.get("data"),
        error=result.get("error"),
    )


@router.get("/history", response_model=Dict[str, Any])
async def query_history():
    """
    查询历史记录（当前会话）。

    注意: 当前版本使用内存存储，重启后清空。
    """
    agent = get_exec_agent()
    memory = agent._executor.memory

    if not memory or not hasattr(memory, "chat_memory"):
        return {"total": 0, "items": []}

    messages = memory.chat_memory.messages
    items = [
        {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
        for msg in messages
    ]

    return {"total": len(items), "items": items}
