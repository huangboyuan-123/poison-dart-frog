# 箭毒蛙 — AI + SQL 数据库操纵工具

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52.svg)](https://doc.qt.io/qtforpython-6/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🐸 箭毒蛙 — 集 AI 自然语言交互、SQL 执行、数据可视编辑于一体的数据库桌面管理工具。支持 MySQL 和 Redis 双数据源。

---

## ✨ 功能亮点

### 🤖 AI 智能助手
- **自然语言 → SQL**：用中文描述需求，AI 自动生成并执行 SQL
- **自然语言 → Redis 命令**：支持 String/Hash/List/Set/ZSet 全类型
- **上下文感知**：自动读取数据库 Schema，生成精准查询

### 🗄️ 数据库管理（类 Navicat 体验）
- **可视化表设计器**：增删改列、修改类型/默认值，自动生成 ALTER TABLE
- **内联数据编辑**：双击单元格直接修改，批量保存/撤销
- **行级操作**：新增行、删除行、外键跳转
- **排序筛选**：表头点击排序、右键快速筛选
- **导入导出**：CSV / Excel / JSON 导入导出

### 🔴 Redis 管理
- **键树浏览**：层级化 Key 展示 + 类型着色
- **值查看编辑**：支持所有数据类型
- **AI 命令生成**：自然语言 → Redis 命令

### 🎨 专业界面
- **PyCharm Darcula 暗色主题**
- **三栏布局**：数据库树 | 数据浏览 | AI 助手
- **可拖拽分割线 + 圆角无边框窗口**

---

## 📸 运行截图

### SQL 执行效果
![SQL执行](运行结果/sql执行效果1.png)

### 查询结果 + AI 分析
![查询结果](运行结果/sql执行结果2.png)

### Redis 模块
![Redis](运行结果/Redis模块.png)

---

## 🚀 快速开始

### 环境要求
- Python >= 3.9
- MySQL 8.0+ / Redis（可选）
- DeepSeek API Key（或其他 OpenAI 兼容接口）

### 安装

```bash
git clone https://gitee.com/huang-baiyuan123/sqlagent.git
cd sqlagent
pip install -e ".[desktop]"
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 填入 API Key 和数据库连接信息
```

或启动后在菜单栏 **设置 → AI 配置** 弹窗中直接修改。

### 启动

**后端 API**：
```bash
uvicorn sqlagent.main:app --host 0.0.0.0 --port 8000 --reload
```

**桌面端**：
```bash
python src/sqlagent/desktop_app.py
```

启动后访问 `http://localhost:8000/docs` 查看 API 文档。

---

## 🏗️ 项目结构

```
sqlagent/
├── src/sqlagent/
│   ├── desktop_app.py       # PySide6 桌面端 (约 2300 行)
│   ├── main.py              # FastAPI 应用入口
│   ├── agent.py             # LangChain AI Agent 核心
│   ├── database.py          # MySQL 数据库管理器
│   ├── tools.py             # Agent 工具集
│   ├── config.py            # 配置管理
│   ├── prompts.py           # AI 提示词模板
│   ├── models.py            # Pydantic 数据模型
│   ├── routers/
│   │   ├── query.py         # /api/query, /api/execute
│   │   ├── schema.py        # /api/schema, /api/databases
│   │   ├── table.py         # /api/table (增删改查)
│   │   ├── redis_routes.py  # /api/redis (键值操作+AI)
│   │   └── health.py        # /health
│   └── static/              # 图标资源
├── tests/                   # 测试
├── .env.example             # 环境变量模板
└── docker-compose.yml       # Docker 部署
```

---

## 🔧 技术栈

| 层 | 技术 |
|---|---|
| 桌面 GUI | PySide6 (Qt for Python) |
| 后端 API | FastAPI + Uvicorn |
| AI Agent | LangChain + DeepSeek / OpenAI |
| 数据库 | SQLAlchemy + PyMySQL |
| Redis | redis-py |
| 语法高亮 | QSyntaxHighlighter |
| Excel | openpyxl |

---

## 📡 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/query` | AI 自然语言 → SQL |
| `POST` | `/api/execute` | 执行 SQL |
| `GET` | `/api/databases` | 列出所有数据库 |
| `GET` | `/api/schema` | 获取表结构 |
| `POST` | `/api/table/update` | 更新行 |
| `POST` | `/api/table/insert` | 插入行 |
| `POST` | `/api/table/delete` | 删除行 |
| `GET` | `/api/table/ddl` | 查看建表 DDL |
| `GET` | `/api/redis/keys` | Redis 键列表 |
| `GET` | `/api/redis/key/{key}` | Redis 键值 |
| `POST` | `/api/redis/query` | Redis AI 命令生成 |
| `POST` | `/api/redis/execute` | 执行 Redis 命令 |

---

## 📄 License

MIT
