"""
FastAPI API 接口测试。

使用 FastAPI TestClient + 内存 SQLite（测试数据库操作逻辑），
不依赖真实 MySQL 连接。
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 设置测试环境变量
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_PASSWORD"] = "test123"

from sqlagent.main import app  # noqa: E402
from sqlagent import __version__  # noqa: E402

client = TestClient(app)


class TestRootEndpoint:
    """根路径测试。"""

    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SQLAgent"
        assert data["version"] == __version__
        assert "docs" in data

    def test_docs_available(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self):
        response = client.get("/redoc")
        assert response.status_code == 200


class TestHealthEndpoint:
    """健康检查接口测试。"""

    @patch("sqlagent.routers.health.SQLAgent")
    def test_health_check(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.test_connections.return_value = {
            "status": "healthy",
            "database": True,
            "llm": True,
        }
        mock_agent_class.return_value = mock_agent

        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] is True
        assert data["llm"] is True
        assert data["version"] == __version__


class TestSchemaEndpoint:
    """Schema 接口测试。"""

    @patch("sqlagent.routers.schema.SQLAgent")
    def test_get_schema(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.db.get_schema.return_value = [
            {
                "table": "users",
                "columns": [
                    {"name": "id", "type": "int(11)", "nullable": False, "key": "PRI", "default": None, "extra": "auto_increment", "data_type": "int"},
                    {"name": "name", "type": "varchar(100)", "nullable": False, "key": "", "default": None, "extra": "", "data_type": "varchar"},
                ],
            }
        ]
        mock_agent.db.engine.url.database = "sqlagent"
        mock_agent_class.return_value = mock_agent

        response = client.get("/api/schema")
        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "sqlagent"
        assert len(data["tables"]) == 1
        assert data["tables"][0]["table"] == "users"

    @patch("sqlagent.routers.schema.SQLAgent")
    def test_get_table_schema(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.db.get_table_info.return_value = {
            "table": "users",
            "columns": [{"name": "id", "type": "int(11)", "nullable": False, "key": "PRI", "default": None, "extra": "auto_increment", "data_type": "int"}],
        }
        mock_agent_class.return_value = mock_agent

        response = client.get("/api/schema/users")
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "users"

    @patch("sqlagent.routers.schema.SQLAgent")
    def test_get_table_not_found(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.db.get_table_info.return_value = None
        mock_agent_class.return_value = mock_agent

        response = client.get("/api/schema/nonexistent")
        assert response.status_code == 404


class TestQueryEndpoint:
    """查询接口测试。"""

    @patch("sqlagent.routers.query.SQLAgent")
    def test_nl_query(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.run.return_value = {
            "success": True,
            "output": "数据库中有以下表：\n```sql\nSELECT TABLE_NAME FROM information_schema.TABLES;\n```\n查询到2个表：users, orders",
        }
        mock_agent_class.return_value = mock_agent

        response = client.post("/api/query", json={"question": "显示所有表"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["question"] == "显示所有表"

    @patch("sqlagent.routers.query.SQLAgent")
    def test_execute_sql(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.db.execute_sql.return_value = {
            "success": True,
            "error": None,
            "data": {"columns": ["id", "name"], "rows": [[1, "Alice"]], "row_count": 1},
        }
        mock_agent_class.return_value = mock_agent

        response = client.post("/api/execute", json={"sql": "SELECT * FROM users LIMIT 1"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["row_count"] == 1


class TestModels:
    """Pydantic 模型验证测试。"""

    def test_query_request_valid(self):
        from sqlagent.models import QueryRequest
        req = QueryRequest(question="查询所有用户")
        assert req.question == "查询所有用户"

    def test_query_request_empty(self):
        from sqlagent.models import QueryRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            QueryRequest(question="")

    def test_execute_request_defaults(self):
        from sqlagent.models import ExecuteRequest
        req = ExecuteRequest(sql="SELECT 1")
        assert req.read_only is True

    def test_health_response(self):
        from sqlagent.models import HealthResponse
        resp = HealthResponse(status="healthy", database=True, llm=True, version="0.2.0")
        assert resp.status == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
