"""
Pydantic 请求/响应数据模型。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── 请求模型 ──────────────────────────────────────────

class QueryRequest(BaseModel):
    """自然语言查询请求。"""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="自然语言问题，例如：查询销售额最高的10个产品",
        examples=["显示所有表", "查询过去30天注册的用户数量"],
    )


class ExecuteRequest(BaseModel):
    """直接 SQL 执行请求。"""

    sql: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="要执行的 SQL 语句",
        examples=["SELECT * FROM users LIMIT 10"],
    )
    read_only: bool = Field(
        default=True,
        description="是否只读模式（默认 true，阻止写操作）",
    )


# ── 响应模型 ──────────────────────────────────────────

class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str = Field(description="整体状态: healthy / unhealthy")
    database: bool = Field(description="数据库连接状态")
    llm: bool = Field(description="LLM 连接状态")
    version: str = Field(description="应用版本")


class SchemaResponse(BaseModel):
    """数据库结构响应。"""

    database: str = Field(description="数据库名称")
    tables: List[Dict[str, Any]] = Field(description="表结构列表")


class QueryResponse(BaseModel):
    """自然语言查询响应。"""

    success: bool = Field(description="查询是否成功")
    question: str = Field(description="原始问题")
    sql: Optional[str] = Field(default=None, description="生成的 SQL 语句")
    data: Optional[Dict[str, Any]] = Field(default=None, description="查询结果数据")
    answer: Optional[str] = Field(default=None, description="AI 分析回答")
    error: Optional[str] = Field(default=None, description="错误信息（如有）")


class ExecuteResponse(BaseModel):
    """SQL 执行响应。"""

    success: bool = Field(description="执行是否成功")
    sql: str = Field(description="执行的 SQL")
    data: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息（如有）")


class HistoryResponse(BaseModel):
    """查询历史响应。"""

    total: int = Field(description="历史记录总数")
    items: List[Dict[str, Any]] = Field(description="历史记录列表")
