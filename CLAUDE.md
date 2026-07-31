# CLAUDE.md

此文件为 Claude Code 在 sqlagent 仓库中工作时提供指导。

## 项目概述

sqlagent 是一个 **FastAPI REST API + LangChain Agent + MySQL** 架构的 AI 数据库操控系统。
通过 HTTP API 将自然语言转换为 SQL 查询并执行，部署在 Docker 容器中。

## 构建、测试、开发命令

- **Docker 部署**: `docker compose up -d`
- **Docker 构建**: `docker compose build`
- **Docker 停止**: `docker compose down`
- **本地开发启动**: `uvicorn sqlagent.main:app --host 0.0.0.0 --port 8000 --reload`
- **安装依赖**: `pip install -e ".[dev]"`
- **运行测试**: `pytest`
- **单个测试**: `pytest tests/test_api.py::test_health_check`
- **覆盖率测试**: `pytest --cov=sqlagent --cov-report=term-missing`
- **代码检查**: `ruff check src/ tests/`
- **类型检查**: `mypy src/`
- **API 文档**: 启动后访问 `http://localhost:8000/docs`
- **启动 MySQL（仅数据库）**: `docker compose up -d mysql`

## 架构

```
API 层 (FastAPI)
┌─────────────────────────────────────────────┐
│ main.py ← routers/health.py, query.py, schema.py │
│   ↕                                         │
│ Agent 层 (LangChain)                         │
│ agent.py → tools.py (4 tools)               │
│   ↕                                         │
│ 数据层 (SQLAlchemy + PyMySQL)                │
│ database.py → MySQL 8.0                     │
└─────────────────────────────────────────────┘
```

```
src/sqlagent/
├── main.py           # FastAPI app, CORS, lifespan, 路由注册
├── models.py         # Pydantic 模型: QueryRequest/Response, HealthResponse 等
├── config.py         # 配置 dataclass: MySQLConfig, LLMConfig, AppConfig
├── database.py       # DatabaseManager: get_schema(), execute_sql(), validate_sql()
├── agent.py          # SQLAgent: run(), stream(), clear_memory(), test_connections()
├── tools.py          # create_tools(db) → [list_tables, get_table_schema, execute_query, validate_sql]
├── prompts.py        # SQL_AGENT_SYSTEM_PROMPT (MySQL 特化)
└── routers/
    ├── health.py     # GET /api/health
    ├── query.py      # POST /api/query, POST /api/execute, GET /api/history
    └── schema.py     # GET /api/schema, GET /api/schema/{table}
```

## 代码规范

- Python >= 3.10, FastAPI 0.115+, LangChain 0.3+
- 类型标注: 所有函数参数和返回值使用 type hints
- 配置: 通过环境变量 / .env 文件，敏感信息不硬编码
- 工具函数: 使用工厂模式 `create_tools(db)` 而非全局变量（避免并发问题）
- 数据库: MySQL only，使用 `information_schema` 获取 Schema
- 安全: 默认只读模式，`_is_read_only()` 检查 SQL 关键字
- Docker: `python:3.11-slim` + `mysql:8.0`，docker-compose 编排

## 关键依赖

| 包 | 版本 | 用途 |
|---|---|---|
| fastapi | 0.115.x | Web 框架 |
| uvicorn | 0.34.x | ASGI 服务器 |
| langchain | 0.3.x | Agent 框架 |
| langchain-openai | 0.2.x | LLM 接口 |
| sqlalchemy | 2.0.x | 数据库抽象 |
| pymysql | 1.1.x | MySQL 驱动 |
| pydantic | 2.10.x | 数据校验 |
