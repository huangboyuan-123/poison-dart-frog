"""
数据库连接与操作工具模块。
"""

from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .config import config


class DatabaseManager:
    """数据库管理器 - 管理连接、Schema 获取、查询执行。"""

    def __init__(self, database_url: str | None = None):
        url = database_url or config.database.url
        self._engine: Engine = create_engine(url, echo=False)

    @property
    def engine(self) -> Engine:
        return self._engine

    def get_schema(self) -> str:
        """获取数据库 Schema 信息（表名和列信息）。"""
        try:
            inspector_query = """
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                ORDER BY table_name, ordinal_position
            """
            with self._engine.connect() as conn:
                result = conn.execute(text(inspector_query))
                rows = result.fetchall()

            if not rows:
                # SQLite fallback
                return self._get_schema_sqlite()

            schema_lines = []
            current_table = None
            for row in rows:
                table, col, dtype, nullable = row
                if table != current_table:
                    if current_table is not None:
                        schema_lines.append("")
                    schema_lines.append(f"表: {table}")
                    current_table = table
                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                schema_lines.append(f"  - {col}: {dtype} ({null_str})")

            return "\n".join(schema_lines)

        except SQLAlchemyError:
            return self._get_schema_sqlite()

    def _get_schema_sqlite(self) -> str:
        """SQLite Schema 获取（回退方案）。"""
        try:
            with self._engine.connect() as conn:
                tables = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                ).fetchall()

            schema_lines = []
            for (table,) in tables:
                schema_lines.append(f"表: {table}")
                cols = conn.execute(text(f"PRAGMA table_info('{table}')"))
                for col in cols:
                    _, name, dtype, not_null, _, _ = col
                    null_str = "NOT NULL" if not_null else "NULL"
                    schema_lines.append(f"  - {name}: {dtype} ({null_str})")
                schema_lines.append("")

            return "\n".join(schema_lines) if schema_lines else "未找到表"

        except SQLAlchemyError as e:
            return f"[Schema 获取失败: {e}]"

    def execute_sql(self, sql: str, read_only: bool = True) -> dict[str, Any]:
        """执行 SQL 语句并返回结果。"""
        if read_only and not self._is_read_only(sql):
            return {
                "success": False,
                "error": "安全限制：当前为只读模式，拒绝执行写操作。",
                "data": None,
            }

        try:
            with self._engine.connect() as conn:
                if read_only:
                    # 只读模式下使用事务并回滚，确保不写入
                    trans = conn.begin()
                    try:
                        result = conn.execute(text(sql))
                        rows = result.fetchall()
                        columns = list(result.keys()) if result.returns_rows else []
                        trans.rollback()
                    except Exception:
                        trans.rollback()
                        raise
                else:
                    result = conn.execute(text(sql))
                    rows = result.fetchall()
                    columns = list(result.keys()) if result.returns_rows else []
                    conn.commit()

                return {
                    "success": True,
                    "error": None,
                    "data": {"columns": columns, "rows": [list(row) for row in rows], "row_count": len(rows)},
                }

        except SQLAlchemyError as e:
            return {"success": False, "error": str(e), "data": None}

    @staticmethod
    def _is_read_only(sql: str) -> bool:
        """检查 SQL 是否为只读查询。"""
        sql_upper = sql.strip().upper()
        # 移除注释和空白
        statements = [s.strip() for s in sql_upper.split(";") if s.strip()]
        write_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
            "ALTER", "TRUNCATE", "RENAME", "REPLACE", "MERGE",
        ]
        for stmt in statements:
            first_word = stmt.split()[0] if stmt.split() else ""
            if first_word in write_keywords:
                return False
        return True

    def test_connection(self) -> bool:
        """测试数据库连接是否正常。"""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False
