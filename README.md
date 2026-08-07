<div align="center">

<img src="src/sqlagent/static/database.png" width="120" alt="logo">

# 🐸 箭毒蛙 Poison Dart Frog

### 下一代 AI 数据库桌面管理工具

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt)](https://doc.qt.io/qtforpython-6/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/AI-LangChain-1C3C3C?logo=langchain)](https://langchain.com)
[![MySQL](https://img.shields.io/badge/DB-MySQL-4479A1?logo=mysql)](https://mysql.com)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis)](https://redis.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/huangboyuan-123/poison-dart-frog?style=social)](https://github.com/huangboyuan-123/poison-dart-frog)

**中文** | [English](#)

</div>

---

## 🔥 为什么是箭毒蛙？

**用嘴写 SQL 的时代来了。**

你不再需要记住 `SELECT * FROM employees WHERE department_id IN (SELECT id FROM departments WHERE name = 'Engineering')`，只需要告诉 AI：

> _"帮我查一下工程部有多少员工，他们的平均工资是多少"_

AI 自动查表结构 → 生成 SQL → 执行 → 返回可视化结果。整个过程不到 3 秒。

---

## ✨ 核心特性

<table>
<tr>
<td width="50%">

### 🤖 AI 自然语言驱动
- 🗣️ **中文输入** → SQL / Redis 命令
- 🧠 **自动查表结构**，无需手写 Schema
- 📝 **流式思考过程**，实时查看 AI 推理
- 🔧 **多步工具调用**：查表→分析→生成→执行
- 🌐 支持 DeepSeek / OpenAI / 任何兼容 API

</td>
<td width="50%">

### 🗄️ Navicat 级数据管理
- 📊 **可视化表设计器**（增删改列，自动生成 DDL）
- ✏️ **内联单元格编辑**（双击即改，批量保存）
- 🔍 **点击表头排序** / 右键筛选
- 🔗 **外键跳转**（点击 FK 值直达引用行）
- 📥📤 **导入导出** CSV / Excel / JSON

</td>
</tr>
<tr>
<td width="50%">

### 🎨 PyCharm 暗色主题
- 🖤 Darcula 配色（#2B2B2B），护眼舒适
- 🐸 箭毒蛙青绿色强调（#00BFA5）
- 💻 JetBrains Mono 字体，代码感十足
- 🪟 无边框圆角窗口 + 四栏可拖拽布局
- 🖱️ 边缘拉伸 + 标题栏拖拽移动

</td>
<td width="50%">

### 🔴 Redis 全功能支持
- 🌳 **键树浏览**（层级化，类型着色）
- 👁️ **值查看/编辑**（String/Hash/List/Set/ZSet）
- 🤖 **AI 命令生成**（自然语言 → Redis 命令）
- 🔒 **类型安全拦截**（Hash 不会用 GET 误查）

</td>
</tr>
</table>

---

## 📸 预览

<p align="center">
  <img src="运行结果/sql执行效果1.png" width="45%" alt="SQL执行">
  &nbsp;&nbsp;
  <img src="运行结果/sql执行结果2.png" width="45%" alt="查询结果">
</p>

<p align="center">
  <img src="运行结果/Redis模块.png" width="45%" alt="Redis模块">
</p>

---

## 🚀 3 分钟快速开始

```bash
# 1. 克隆
git clone https://github.com/huangboyuan-123/poison-dart-frog.git
cd poison-dart-frog

# 2. 安装
pip install -e ".[desktop]"

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=sk-xxx

# 4. 启动后端
uvicorn sqlagent.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 启动桌面端（新终端）
python src/sqlagent/desktop_app.py
```

> 💡 没有 MySQL？Docker 一键启动：`docker compose up -d mysql`

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   PySide6 桌面端                      │
│  ┌──────┬────────────┬────────────┬──────────┐      │
│  │ A 树 │  B 数据浏览 │  C AI 助手  │ D 思考    │      │
│  └──────┴────────────┴────────────┴──────────┘      │
│         QThread 异步  │  QSyntaxHighlighter         │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP (localhost:8000)
┌──────────────────▼──────────────────────────────────┐
│                  FastAPI 后端                         │
│  ┌─────────┬──────────┬──────────┬──────────┐       │
│  │ /query  │ /execute │ /schema  │ /table   │       │
│  │ /redis  │ /health  │ /stream  │ /ddl     │       │
│  └─────────┴──────────┴──────────┴──────────┘       │
│         LangChain Agent  │  SQLAlchemy              │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              MySQL 8.0  │  Redis 7.0                 │
└─────────────────────────────────────────────────────┘
```

---

## 📡 API 一览

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/query` | 🤖 自然语言 → SQL |
| `POST` | `/api/query/stream` | 📡 流式 AI 思考 |
| `POST` | `/api/execute` | ⚡ 执行 SQL |
| `GET` | `/api/databases` | 📊 列出所有数据库 |
| `GET` | `/api/schema` | 📋 表结构 |
| `POST` | `/api/table/update` | ✏️ 更新行 |
| `POST` | `/api/table/insert` | ➕ 插入行 |
| `POST` | `/api/table/delete` | 🗑 删除行 |
| `DELETE` | `/api/table/drop` | 💣 删表 |
| `GET` | `/api/redis/keys` | 🔑 键列表 |
| `POST` | `/api/redis/query` | 🤖 Redis AI |

---

## 🧩 项目结构

```
poison-dart-frog/
├── src/sqlagent/
│   ├── desktop/            # PySide6 桌面端模块
│   │   ├── dialogs/        # 弹窗(连接/设计器/设置)
│   │   ├── panels/         # A/B/C/D 四栏面板
│   │   ├── main_window.py  # 主窗口
│   │   └── main.py         # 入口
│   ├── routers/            # FastAPI 路由
│   │   ├── query.py        # AI查询 + 流式
│   │   ├── table.py        # 表CRUD + DROP
│   │   ├── schema.py       # 数据库结构
│   │   ├── redis_routes.py # Redis 全功能
│   │   └── health.py       # 健康检查
│   ├── agent.py            # LangChain Agent
│   ├── database.py         # MySQL 管理器
│   ├── tools.py            # Agent 工具集
│   ├── prompts.py          # AI 提示词
│   └── static/             # 图标资源
├── tests/                  # 测试
├── docker-compose.yml      # Docker 部署
└── .env.example            # 配置模板
```

---

## 🌟 Star History

如果这个项目对你有用，请给一颗 ⭐ Star！你的支持是我持续更新的动力。

<a href="https://star-history.com/#huangboyuan-123/poison-dart-frog&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangboyuan-123/poison-dart-frog&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangboyuan-123/poison-dart-frog&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangboyuan-123/poison-dart-frog&type=Date" />
  </picture>
</a>

---

## 📄 License

MIT © 2025 [会飞的程序源](https://github.com/huangboyuan-123)

