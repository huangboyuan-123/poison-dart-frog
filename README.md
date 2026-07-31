# SQLAgent

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🤖 AI 驱动的 SQL 智能代理 — 用自然语言与数据库交互

SQLAgent 是一个基于大语言模型 (LLM) 的 SQL 智能代理，能够将自然语言查询转换为 SQL 语句，执行数据库操作，并生成可读的结果分析。

## ✨ 功能特性

- 🗣️ **自然语言转 SQL** — 用日常语言描述需求，自动生成并执行 SQL
- 🧠 **智能上下文理解** — 自动读取数据库 Schema，理解表结构和关系
- 🔄 **多轮对话** — 支持连续对话，逐步细化查询需求
- 📊 **结果分析** — 对查询结果进行智能总结和可视化建议
- 🔌 **多数据库支持** — MySQL、PostgreSQL、SQLite、SQL Server
- 🛡️ **安全模式** — 支持只读模式，防止误操作修改数据
- 📝 **查询历史** — 记录所有查询，支持回溯和复用

## 🚀 快速开始

### 环境要求

- Python >= 3.10
- 一个 OpenAI 兼容的 API Key

### 安装

```bash
# 克隆仓库
git clone https://gitee.com/huang-baiyuan123/sqlagent.git
cd sqlagent

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -e .
```

### 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入你的 API Key 和数据库连接
```

### 使用

```bash
# 启动交互式 CLI
sqlagent

# 或者直接查询
sqlagent query "查询过去30天销售额最高的10个产品"
```

## 🏗️ 项目结构

```
sqlagent/
├── src/sqlagent/          # 核心代码
│   ├── __init__.py
│   ├── __main__.py        # CLI 入口
│   ├── agent.py           # AI Agent 核心逻辑
│   ├── database.py        # 数据库连接与工具
│   ├── prompts.py         # 系统提示词
│   ├── tools.py           # Agent 工具集
│   └── config.py          # 配置管理
├── tests/                 # 测试
├── examples/              # 使用示例
├── pyproject.toml         # 项目元数据
├── requirements.txt       # 依赖列表
└── .env.example           # 环境变量模板
```

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE)
