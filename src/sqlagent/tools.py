"""
Agent 工具集模块 — 定义 AI Agent 可调用的工具。
"""

from typing import Any

from langchain.tools import tool

from sqlalchemy import text

from .database import DatabaseManager

# 全局数据库管理器（由 Agent 初始化时注入）
_db_manager: DatabaseManager | None = None


def set_db_manager(manager: DatabaseManager) -> None:
    """设置全局数据库管理器。"""
    global _db_manager
    _db_manager = manager


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器。"""
    if _db_manager is None:
        raise RuntimeError("数据库管理器未初始化，请先调用 set_db_manager()")
    return _db_manager


@tool
def list_tables() -> str:
    """列出数据库中所有的表名。调用此工具来了解数据库中有哪些表可用。"""
    db = get_db_manager()
    try:
        with db.engine.connect() as conn:
            # 跨数据库兼容的获取表名方式
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if not tables:
                return "数据库中未找到任何表。"
            return "数据库中的表:\n" + "\n".join(f"  - {t}" for t in tables)
    except Exception as e:
        return f"获取表列表失败: {e}"


@tool
def get_table_schema(table_name: str) -> str:
    """获取指定表的完整结构信息（列名、数据类型、是否可为空）。

    Args:
        table_name: 要查看结构的表名
    """
    db = get_db_manager()
    try:
        with db.engine.connect() as conn:
            from sqlalchemy import inspect, text

            inspector = inspect(db.engine)
            columns = inspector.get_columns(table_name)

            if not columns:
                return f"表 '{table_name}' 不存在或没有列信息。"

            lines = [f"表: {table_name}"]
            for col in columns:
                name = col["name"]
                dtype = str(col["type"])
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                default = col.get("default")
                pk = "PRIMARY KEY" if col.get("primary_key") else ""
                extra = " ".join(filter(None, [pk]))
                if extra:
                    extra = f" [{extra}]"
                lines.append(f"  - {name}: {dtype} ({nullable}){extra}")
                if default:
                    lines.append(f"    默认值: {default}")

            return "\n".join(lines)
    except Exception as e:
        return f"获取表结构失败: {e}"


@tool
def execute_query(sql: str) -> str:
    """执行 SQL 查询并返回结果。只支持 SELECT 查询。

    Args:
        sql: 要执行的 SQL 查询语句（仅限 SELECT）
    """
    db = get_db_manager()
    result = db.execute_sql(sql, read_only=True)

    if not result["success"]:
        return f"查询执行失败: {result['error']}"

    data = result["data"]
    if not data or not data["columns"]:
        return "查询已执行，但没有返回结果。"

    # 格式化输出
    columns = data["columns"]
    rows = data["rows"]
    row_count = data["row_count"]

    lines = [
        f"查询成功，返回 {row_count} 行数据。",
        f"列: {', '.join(columns)}",
        "-" * 60,
    ]

    # 限制显示行数
    display_rows = rows[:50]
    for row in display_rows:
        lines.append(str(row))

    if row_count > 50:
        lines.append(f"... 仅显示前 50 行，共 {row_count} 行")

    return "\n".join(lines)


@tool
def validate_sql(sql: str) -> str:
    """验证 SQL 语句的语法是否正确（不实际执行）。

    Args:
        sql: 要验证的 SQL 语句
    """
    db = get_db_manager()
    try:
        with db.engine.connect() as conn:
            # 使用 EXPLAIN 验证语法而不执行
            conn.execute(text(f"EXPLAIN {sql}"))
            # 回滚以确保不会有副作用
            conn.rollback()
            return "SQL 语法验证通过。"
    except Exception as e:
        return f"SQL 语法错误: {e}"



def create_tools(manager: DatabaseManager) -> list:
    """创建并返回 Agent 工具列表。"""
    set_db_manager(manager)
    return [list_tables, get_table_schema, execute_query, validate_sql]
