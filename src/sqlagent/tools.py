"""
LangChain Agent 工具集 — MySQL 数据库交互工具。

每个工具都是独立的 @tool 函数，通过闭包捕获 DatabaseManager 实例。
"""

from collections.abc import Callable

from langchain.tools import tool

from .database import DatabaseManager


def _make_tools(db: DatabaseManager, include_execute: bool) -> list:
    """创建工具集。include_execute=False 时仅生成 SQL 不执行。"""

    @tool
    def list_tables() -> str:
        """列出数据库中所有的表名。在不确定有哪些表时首先调用。"""
        try:
            schema = db.get_schema()
            if not schema:
                return "数据库中未找到任何表。"
            table_names = [t["table"] for t in schema]
            return "数据库中的表:\n" + "\n".join(f"  - {name}" for name in table_names)
        except Exception as e:
            return f"获取表列表失败: {e}"

    @tool
    def get_table_schema(table_name: str) -> str:
        """获取指定表的完整结构：列名、类型、是否可空、键信息。"""
        try:
            info = db.get_table_info(table_name)
            if not info:
                return f"表 '{table_name}' 不存在。"
            lines = [f"表: {table_name}"]
            for col in info["columns"]:
                null = "NULL" if col["nullable"] else "NOT NULL"
                key = ""
                if col["key"] == "PRI": key = " [PRIMARY KEY]"
                elif col["key"] == "MUL": key = " [INDEX/FK]"
                elif col["key"] == "UNI": key = " [UNIQUE]"
                default = f" DEFAULT {col['default']}" if col["default"] else ""
                extra = f" {col['extra']}" if col["extra"] else ""
                lines.append(f"  - {col['name']}: {col['type']} ({null}){key}{default}{extra}")
            return "\n".join(lines)
        except Exception as e:
            return f"获取表结构失败: {e}"

    @tool
    def execute_query(sql: str) -> str:
        """执行 SQL 查询并返回结果（仅限 SELECT）。"""
        result = db.execute_sql(sql, read_only=True)
        if not result["success"]:
            return f"查询执行失败: {result['error']}"
        data = result["data"]
        if not data or not data["columns"]:
            return "查询已执行，但没有返回数据。"
        cols = data["columns"]
        rows = data["rows"]
        out = [f"查询成功，返回 {data['row_count']} 行。", f"列: {', '.join(cols)}", "-" * 50]
        for row in rows[:50]:
            out.append(str(tuple(row)))
        if data['row_count'] > 50:
            out.append(f"... (仅显示前 50 行，共 {data['row_count']} 行)")
        return "\n".join(out)

    @tool
    def validate_sql(sql: str) -> str:
        """验证 SQL 语句的语法是否正确（使用 EXPLAIN，不实际执行）。"""
        result = db.validate_sql(sql)
        if result["valid"]:
            return f"SQL 语法验证通过。\n执行计划:\n{result['plan']}"
        return f"SQL 语法错误: {result['error']}"

    tools = [list_tables, get_table_schema, validate_sql]
    if include_execute:
        tools.append(execute_query)
    return tools


def create_tools(db: DatabaseManager) -> list:
    """创建完整的 Agent 工具列表（含 execute_query）。"""
    return _make_tools(db, include_execute=True)


def create_query_tools(db: DatabaseManager) -> list:
    """创建仅用于 SQL 生成的工具（不含 execute_query）。

    生成阶段只能查看表结构 + 验证语法，不能执行 SQL。
    执行由用户手动通过 /api/execute 触发。
    """
    return _make_tools(db, include_execute=False)
