"""
FastAPI 应用入口 — SQLAgent REST API 服务。

启动方式:
    uvicorn sqlagent.main:app --host 0.0.0.0 --port 8000 --reload
    python -m sqlagent

API 文档:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console

from . import __version__
from .routers import health, query, schema

console = Console()

# ── 应用生命周期 ──────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用启动/关闭时的生命周期管理。"""
    console.print(f"[bold cyan]🤖 SQLAgent v{__version__} 启动中...[/bold cyan]")

    # 预热：创建 Agent 实例
    try:
        from .agent import SQLAgent
        agent = SQLAgent()
        db_ok = agent.db.test_connection()
        if db_ok:
            console.print("[green]  ✅ 数据库连接成功[/green]")
        else:
            console.print("[yellow]  ⚠️  数据库连接失败 — 请检查 MySQL 配置[/yellow]")
    except Exception as e:
        console.print(f"[yellow]  ⚠️  Agent 初始化失败: {e}[/yellow]")

    console.print(f"[bold green]  🚀 API 服务已启动: http://0.0.0.0:8000[/bold green]")
    console.print(f"  📖 Swagger 文档: http://localhost:8000/docs")

    yield  # 应用运行中

    console.print("[yellow]SQLAgent 正在关闭...[/yellow]")


# ── 创建 FastAPI 应用 ─────────────────────────────────

app = FastAPI(
    title="SQLAgent API",
    description="AI 驱动的 MySQL 数据库操控 Agent — 用自然语言查询数据库",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(query.router)
app.include_router(schema.router)


# ── 根路径 ────────────────────────────────────────────

@app.get("/")
async def root():
    """API 根路径 — 返回服务信息。"""
    return {
        "name": "SQLAgent",
        "version": __version__,
        "description": "AI 驱动的 MySQL 数据库操控 Agent",
        "docs": "/docs",
        "health": "/api/health",
    }
