"""
SQLAgent 核心功能测试。
"""

import pytest
from sqlalchemy import create_engine, text

from sqlagent.agent import SQLAgent
from sqlagent.database import DatabaseManager
from sqlagent.config import config


class TestDatabaseManager:
    """数据库管理器测试。"""

    @pytest.fixture
    def db(self):
        """创建内存 SQLite 数据库用于测试。"""
        manager = DatabaseManager("sqlite:///:memory:")
        # 创建测试表
        with manager.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            conn.execute(text("INSERT INTO users VALUES (1, 'Alice', 'alice@test.com', '2024-01-01')"))
            conn.execute(text("INSERT INTO users VALUES (2, 'Bob', 'bob@test.com', '2024-01-02')"))
            conn.execute(text("INSERT INTO orders VALUES (1, 1, 99.9, '2024-02-01')"))
            conn.execute(text("INSERT INTO orders VALUES (2, 1, 50.0, '2024-02-02')"))
            conn.execute(text("INSERT INTO orders VALUES (3, 2, 200.0, '2024-02-03')"))
            conn.commit()
        return manager

    def test_test_connection(self, db):
        """测试数据库连接。"""
        assert db.test_connection() is True

    def test_get_schema(self, db):
        """测试获取 Schema。"""
        schema = db.get_schema()
        assert "users" in schema
        assert "orders" in schema

    def test_execute_select(self, db):
        """测试执行 SELECT 查询。"""
        result = db.execute_sql("SELECT * FROM users")
        assert result["success"] is True
        assert result["data"]["row_count"] == 2

    def test_execute_write_blocked(self, db):
        """测试只读模式阻止写操作。"""
        result = db.execute_sql("INSERT INTO users VALUES (3, 'Eve', 'eve@test.com', '2024-01-03')", read_only=True)
        assert result["success"] is False
        assert "只读模式" in result["error"]

    def test_execute_write_allowed(self, db):
        """测试非只读模式允许写操作。"""
        result = db.execute_sql(
            "INSERT INTO users VALUES (3, 'Eve', 'eve@test.com', '2024-01-03')",
            read_only=False,
        )
        assert result["success"] is True

    def test_is_read_only(self, db):
        """测试只读检测逻辑。"""
        assert db._is_read_only("SELECT * FROM users") is True
        assert db._is_read_only("INSERT INTO users VALUES (1)") is False
        assert db._is_read_only("UPDATE users SET name='X'") is False
        assert db._is_read_only("DELETE FROM users") is False
        assert db._is_read_only("DROP TABLE users") is False


class TestSQLAgent:
    """SQLAgent 核心测试。"""

    def test_agent_creation(self):
        """测试 Agent 创建。"""
        agent = SQLAgent(database_url="sqlite:///:memory:")
        assert agent is not None
        assert agent._db_manager is not None
        assert agent._llm is not None
        assert len(agent._tools) > 0

    def test_db_property(self):
        """测试数据库管理器属性。"""
        agent = SQLAgent(database_url="sqlite:///:memory:")
        assert isinstance(agent.db, DatabaseManager)

    def test_clear_memory(self):
        """测试清除记忆。"""
        agent = SQLAgent(database_url="sqlite:///:memory:")
        agent.clear_memory()
        # 验证记忆已清除
        memory = agent._agent_executor.memory
        assert len(memory.chat_memory.messages) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
