"""
MySQL 数据库管理器 — 连接管理、Schema 获取、SQL 执行。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from .config import config


class DatabaseManager:
    """MySQL 数据库管理器。

    使用 SQLAlchemy 2.0 + PyMySQL 驱动，
    提供 Schema 获取、SQL 执行、安全检查等功能。

    用法:
        db = DatabaseManager()
        schema = db.get_schema()
        result = db.execute_sql("SELECT * FROM users LIMIT 5")
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        初始化数据库管理器。

        Args:
            database_url: MySQL 连接 URL，默认使用 .env 配置。
                          格式: mysql+pymysql://user:pass@host:port/db
        """
        url = database_url or config.mysql.url
        self._engine: Engine = create_engine(
            url,
            echo=False,
            pool_size=5,
            pool_recycle=3600,       # 1小时后回收连接 (避免 MySQL 8小时断开)
            pool_pre_ping=True,       # 每次使用前 ping 检测连接有效性
            connect_args={"charset": "utf8mb4"},
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def get_databases(self) -> List[str]:
        """获取 MySQL 服务器上所有数据库(排除系统库)。"""
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(text(
                    "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                    "WHERE SCHEMA_NAME NOT IN "
                    "('information_schema','mysql','performance_schema','sys') "
                    "ORDER BY SCHEMA_NAME"
                )).fetchall()
                return [r[0] for r in rows]
        except SQLAlchemyError:
            return []

    def get_schema(self, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取当前数据库所有用户表的完整结构信息。

        Returns:
            [{"table": "users", "columns": [
                {"name": "id", "type": "int", "nullable": False, "key": "PRI", "default": None},
                ...
            ]}, ...]
        """
        try:
            with self._engine.connect() as conn:
                db_name = database or conn.execute(text("SELECT DATABASE()")).scalar()

                # 查询 information_schema 获取所有表和列
                col_query = text("""
                    SELECT
                        TABLE_NAME,
                        COLUMN_NAME,
                        DATA_TYPE,
                        COLUMN_TYPE,
                        IS_NULLABLE,
                        COLUMN_KEY,
                        COLUMN_DEFAULT,
                        EXTRA,
                        ORDINAL_POSITION
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = :db
                    ORDER BY TABLE_NAME, ORDINAL_POSITION
                """)
                rows = conn.execute(col_query, {"db": db_name}).fetchall()

            # 按表名分组整理
            tables: Dict[str, List[dict]] = {}
            for row in rows:
                table_name = row.TABLE_NAME
                if table_name not in tables:
                    tables[table_name] = []
                tables[table_name].append({
                    "name": row.COLUMN_NAME,
                    "type": row.COLUMN_TYPE,
                    "data_type": row.DATA_TYPE,
                    "nullable": row.IS_NULLABLE == "YES",
                    "key": row.COLUMN_KEY or "",
                    "default": str(row.COLUMN_DEFAULT) if row.COLUMN_DEFAULT is not None else None,
                    "extra": row.EXTRA or "",
                })

            return [
                {"table": table_name, "columns": columns}
                for table_name, columns in tables.items()
            ]

        except SQLAlchemyError as e:
            raise RuntimeError(f"获取数据库 Schema 失败: {e}") from e

    def get_table_info(self, table_name: str, database: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取指定表的详细结构。

        Args:
            table_name: 表名

        Returns:
            表结构字典，不存在则返回 None
        """
        schema = self.get_schema(database)
        for t in schema:
            if t["table"] == table_name:
                return t
        return None

    def format_schema_text(self) -> str:
        """
        将 Schema 格式化为 LLM 可读的文本（用于 Agent 提示词）。

        Returns:
            格式化的文本，如:
            表: users
              - id: int(11) (NOT NULL) [PRIMARY KEY]
              - name: varchar(100) (NOT NULL)
        """
        schema = self.get_schema()
        if not schema:
            return "数据库中未找到任何表。"

        lines = [f"数据库中有 {len(schema)} 个表:\n"]
        for table_info in schema:
            table_name = table_info["table"]
            lines.append(f"表: {table_name}")
            for col in table_info["columns"]:
                null = "NULL" if col["nullable"] else "NOT NULL"
                key_info = ""
                if col["key"] == "PRI":
                    key_info = " [PRIMARY KEY]"
                elif col["key"] == "MUL":
                    key_info = " [FOREIGN KEY / INDEX]"
                elif col["key"] == "UNI":
                    key_info = " [UNIQUE]"
                default = f" DEFAULT {col['default']}" if col["default"] else ""
                extra = f" {col['extra']}" if col["extra"] else ""
                lines.append(
                    f"  - {col['name']}: {col['type']} ({null}){key_info}{default}{extra}"
                )
            lines.append("")

        return "\n".join(lines)

    def execute_sql(self, sql: str, read_only: bool = True) -> Dict[str, Any]:
        """
        执行 SQL 语句并返回结构化结果。

        Args:
            sql: 要执行的 SQL 语句
            read_only: 是否只读模式（True 时拒绝写操作）
        """
        # 预处理: 移除 USE 语句 (REST API 不支持跨请求会话)
        import re as _re
        sql = _re.sub(r'USE\s+\w+\s*;', '', sql, flags=_re.IGNORECASE).strip()
        if not sql:
            return {"success": False, "error": "SQL 为空（已移除无效的 USE 语句，请使用 database.table 格式）", "data": None}

        if read_only and not self._is_read_only(sql):
            return {
                "success": False,
                "error": "安全限制：当前为只读模式，拒绝执行写操作 (INSERT/UPDATE/DELETE/DROP/ALTER 等)。",
                "data": None,
            }

        try:
            with self._engine.connect() as conn:
                affected = 0
                if read_only:
                    trans = conn.begin()
                    try:
                        result = conn.execute(text(sql))
                        if result.returns_rows:
                            rows = [list(row) for row in result.fetchall()]
                            columns = list(result.keys())
                        else:
                            rows, columns = [], []
                            affected = result.rowcount
                        trans.rollback()
                    except Exception:
                        trans.rollback()
                        raise
                else:
                    result = conn.execute(text(sql))
                    if result.returns_rows:
                        rows = [list(row) for row in result.fetchall()]
                        columns = list(result.keys())
                    else:
                        rows, columns = [], []
                        affected = result.rowcount
                    conn.commit()

                return {
                    "success": True,
                    "error": None,
                    "data": {
                        "columns": columns,
                        "rows": rows,
                        "row_count": len(rows) or affected,
                    },
                }

        except SQLAlchemyError as e:
            return {"success": False, "error": str(e), "data": None}

    def execute_sql_raw(self, sql_stmt, read_only: bool = True) -> Dict[str, Any]:
        """执行参数化的 SQLAlchemy text() 语句（防SQL注入）。"""
        try:
            with self._engine.connect() as conn:
                if read_only:
                    trans = conn.begin()
                    try:
                        result = conn.execute(sql_stmt)
                        if result.returns_rows:
                            rows = [list(row) for row in result.fetchall()]
                            columns = list(result.keys())
                            affected = 0
                        else:
                            rows, columns = [], []
                            affected = result.rowcount
                        trans.rollback()
                    except Exception:
                        trans.rollback()
                        raise
                else:
                    result = conn.execute(sql_stmt)
                    if result.returns_rows:
                        rows = [list(row) for row in result.fetchall()]
                        columns = list(result.keys())
                        affected = 0
                    else:
                        rows, columns = [], []
                        affected = result.rowcount
                    conn.commit()

                return {
                    "success": True, "error": None,
                    "data": {"columns": columns, "rows": rows, "row_count": len(rows) or affected},
                }
        except SQLAlchemyError as e:
            return {"success": False, "error": str(e), "data": None}

    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        验证 SQL 语法（使用 EXPLAIN 而不实际执行）。

        Args:
            sql: 要验证的 SQL

        Returns:
            {"valid": bool, "error": str | None, "plan": str | None}
        """
        try:
            with self._engine.connect() as conn:
                # 对于写操作，在事务中 EXPLAIN 后回滚
                trans = conn.begin()
                try:
                    result = conn.execute(text(f"EXPLAIN {sql}"))
                    plan_rows = result.fetchall()
                    plan = "\n".join(str(row) for row in plan_rows)
                    trans.rollback()
                except Exception:
                    trans.rollback()
                    raise

            return {"valid": True, "error": None, "plan": plan}
        except SQLAlchemyError as e:
            return {"valid": False, "error": str(e), "plan": None}

    def test_connection(self) -> bool:
        """测试数据库连接是否正常。"""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except OperationalError:
            return False

    @staticmethod
    def _is_read_only(sql: str) -> bool:
        """
        检查 SQL 是否为只读操作。

        通过对 SQL 分词并检查第一个关键字来判断。
        """
        sql_upper = sql.strip().upper()
        # 移除注释（简单处理：去掉 /* */ 和 -- 注释）
        import re
        sql_clean = re.sub(r"/\*.*?\*/", "", sql_upper, flags=re.DOTALL)
        sql_clean = re.sub(r"--[^\n]*", "", sql_clean)

        statements = [s.strip() for s in sql_clean.split(";") if s.strip()]
        write_keywords = {
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
            "ALTER", "TRUNCATE", "RENAME", "REPLACE", "MERGE",
            "GRANT", "REVOKE", "SET",
        }

        for stmt in statements:
            # 跳过 WITH 前缀 (CTE)
            tokens = stmt.split()
            first_word = tokens[0] if tokens else ""

            # WITH CTE: 跳过 CTE 定义，找实际操作动词
            if first_word == "WITH" and len(tokens) > 1:
                # 跳过 AS (...) 部分，检查 CTE 后的实际语句
                # 简化为: 如果 SQL 包含写关键字则拒绝
                for kw in write_keywords:
                    if kw in stmt.upper():
                        return False
                return True

            if first_word in write_keywords:
                return False

        return True
