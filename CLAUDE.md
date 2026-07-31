# CLAUDE.md

此文件为 Claude Code 在 sqlagent 仓库中工作时提供指导。

## 项目概述

sqlagent 是一个基于 LangChain + LLM（OpenAI 兼容接口）的 Python AI Agent，将自然语言转换为 SQL 查询并执行，返回智能分析结果。

## 构建、测试和开发命令

- **安装开发依赖**: `pip install -e ".[dev]"`
- **运行测试**: `pytest`
- **单个测试**: `pytest tests/test_agent.py::TestDatabaseManager::test_execute_select`
- **覆盖率测试**: `pytest --cov=sqlagent --cov-report=term-missing`
- **代码检查**: `ruff check src/ tests/`
- **类型检查**: `mypy src/`
- **启动 CLI**: `python -m sqlagent`
- **单次查询**: `python -m sqlagent query "查询所有用户"`
- **查看 Schema**: `python -m sqlagent schema`
- **测试连接**: `python -m sqlagent test`

## 架构

```
src/sqlagent/
├── __init__.py       # 版本号
├── __main__.py       # CLI 入口 (argparse, 交互式/单次查询/schema/test)
├── agent.py          # 核心 Agent: 创建 LLM, tools, LangChain AgentExecutor
├── config.py         # 配置管理: pydantic dataclass + python-dotenv
├── database.py       # 数据库管理器: 连接, Schema获取, SQL执行, 安全检查
├── prompts.py        # 系统提示词模板
└── tools.py          # LangChain 工具: list_tables, get_table_schema, execute_query, validate_sql
```

## 代码规范

- 遵循 PEP 8，ruff 强制执行
- 所有公共函数使用类型标注
- 配置通过环境变量 / .env 文件，敏感信息不硬编码
- LangChain 模式: 使用 `@tool` 装饰器定义工具
- 工具返回字符串（LangChain 约定，错误也返回字符串）
- CLI 使用 Rich 库输出美观的终端界面
- 默认只读模式 — 写操作需用户明确确认

## 关键依赖

- **langchain** + **langchain-openai**: Agent 框架和 LLM 集成
- **sqlalchemy**: 数据库抽象层
- **pydantic** + **python-dotenv**: 配置和数据模型
- **rich**: 终端格式化输出
- **click**: CLI 框架（备用）
