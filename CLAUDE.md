# CLAUDE.md

此文件为 Claude Code 在 sqlagent（箭毒蛙）仓库中工作时提供指导。

## 项目概述

箭毒蛙是一个 **FastAPI REST API + LangChain Agent + MySQL/Redis + PySide6 桌面端** 的 AI 数据库操控系统。

## 构建、测试、开发命令

- **启动后端**: `uvicorn sqlagent.main:app --host 0.0.0.0 --port 8000 --reload`
- **启动桌面端**: `python src/sqlagent/desktop_app.py`
- **Docker 部署**: `docker compose up -d`
- **安装依赖**: `pip install -e ".[dev,desktop]"`
- **运行测试**: `pytest`
- **代码检查**: `ruff check src/ tests/`

## 架构

```
桌面端 (PySide6) ←HTTP→ FastAPI ←→ LangChain Agent ←→ MySQL/Redis
     │                    │
  QThread异步          SQLAlchemy + PyMySQL
  QPainter圆角         redis-py
  QSyntaxHighlighter
```

```
src/sqlagent/
├── desktop_app.py       # PySide6 桌面端 (~2300行, 单文件)
├── main.py              # FastAPI app, CORS, lifespan, 路由注册
├── agent.py             # SQLAgent: run(), stream(), test_connections()
├── database.py          # DatabaseManager: get_schema(), execute_sql(), execute_sql_raw()
├── tools.py             # create_tools / create_query_tools (双工具集)
├── config.py            # MySQLConfig, LLMConfig, AppConfig
├── prompts.py           # SQL_AGENT_SYSTEM_PROMPT
├── models.py            # Pydantic 请求/响应模型
└── routers/
    ├── health.py        # GET /health (Agent单例复用)
    ├── query.py         # POST /api/query (无execute工具), POST /api/execute
    ├── schema.py        # GET /api/databases, /api/schema
    ├── table.py         # POST /api/table/update|insert|delete (参数化查询)
    └── redis_routes.py  # Redis 键操作 + AI命令生成/执行
```

## 代码规范

- Python >= 3.9, FastAPI + LangChain + PySide6
- 类型标注: 使用 `Optional[X]` 而非 `X | None`
- 桌面端所有 HTTP 在 QThread 后台线程，通过 Signal 回主线程
- 表操作使用 SQLAlchemy `text().bindparams()` 参数化查询
- Agent 工具集分两套: query模式(无execute) / exec模式(完整)

## 配色 (PyCharm Darcula)

- BG: #2B2B2B, Panel: #3C3F41, Input: #3C3F41
- Accent: #4A88C7, Text: #A9B7C6, Muted: #808080
- Font: JetBrains Mono / Consolas
