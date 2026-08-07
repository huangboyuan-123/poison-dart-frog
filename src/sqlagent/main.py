"""
箭毒蛙 — Redis 专用版 API 入口
启动: uvicorn dendrobates.main:app --host 0.0.0.0 --port 8000 --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .routers import health, redis_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Dendrobates API",
    description="箭毒蛙 — Redis AI 数据库管理工具",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(health.router)
app.include_router(redis_routes.router)


@app.get("/")
async def root():
    return {"name": "Dendrobates", "version": __version__, "docs": "/docs"}
