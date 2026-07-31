# SQLAgent

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🤖 AI 驱动的 MySQL 数据库操控 Agent — REST API 接口，用自然语言查询数据库

SQLAgent 是一个基于 **FastAPI + LangChain + MySQL** 的智能数据库操控系统。提供 HTTP API 接口，将自然语言转换为 SQL 并执行，返回结构化结果。

## ✨ 功能

- 🗣️ **自然语言转 SQL** — 用日常语言描述需求，自动生成 MySQL 查询
- 🔌 **REST API 接口** — FastAPI 构建，Swagger 自动文档
- 🧠 **LangChain Agent** — LLM 驱动的智能工具调用链
- 🐳 **Docker 一键部署** — docker-compose 编排 API + MySQL
- 🛡️ **安全只读模式** — 默认阻止写操作，生产安全
- 📊 **Schema 自动分析** — 自动读取 information_schema，理解表结构

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone https://gitee.com/huang-baiyuan123/sqlagent.git
cd sqlagent

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY

# 3. 启动服务
docker compose up -d

# 4. 验证
curl http://localhost:8000/api/health
# {"status":"healthy","database":true,"llm":true,"version":"0.2.0"}
```

### 本地开发

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动 MySQL（Docker）
docker compose up -d mysql

# 修改 .env 中 MYSQL_HOST=localhost

# 启动 API 服务
uvicorn sqlagent.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📖 API 文档

启动后访问 http://localhost:8000/docs 查看完整 Swagger 文档。

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/query` | 自然语言查询 |
| `POST` | `/api/execute` | 直接执行 SQL |
| `GET` | `/api/schema` | 获取所有表结构 |
| `GET` | `/api/schema/{table}` | 获取指定表结构 |
| `GET` | `/api/history` | 查询对话历史 |

### 示例

```bash
# 自然语言查询
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "显示所有表"}'

# 直接执行 SQL
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users LIMIT 5"}'

# 查看数据库结构
curl http://localhost:8000/api/schema
```

## 🏗️ 项目结构

```
sqlagent/
├── src/sqlagent/          # 核心代码
│   ├── main.py            # FastAPI 应用入口
│   ├── models.py          # Pydantic 请求/响应模型
│   ├── config.py          # MySQL + LLM 配置管理
│   ├── database.py        # 数据库管理器 (Schema获取/SQL执行)
│   ├── agent.py           # LangChain Agent 核心
│   ├── tools.py           # Agent 工具 (list_tables/execute_query/...)
│   ├── prompts.py         # 系统提示词
│   └── routers/           # API 路由
│       ├── health.py      # /api/health
│       ├── query.py       # /api/query + /api/execute
│       └── schema.py      # /api/schema
├── sql/init.sql           # MySQL 初始化脚本
├── tests/                 # 测试
├── Dockerfile
├── docker-compose.yml     # API + MySQL 双容器编排
├── pyproject.toml
└── .env.example
```

## 🔧 配置

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `OPENAI_API_KEY` | — | **必填** OpenAI API Key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API 地址 |
| `OPENAI_MODEL` | `gpt-4o` | 模型名称 |
| `MYSQL_HOST` | `mysql` (Docker) / `localhost` (本地) | MySQL 主机 |
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `MYSQL_USER` | `root` | 数据库用户 |
| `MYSQL_PASSWORD` | `root123` | 数据库密码 |
| `MYSQL_DATABASE` | `sqlagent` | 数据库名 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `READ_ONLY` | `true` | 只读模式 |

## 📄 许可证

MIT License
