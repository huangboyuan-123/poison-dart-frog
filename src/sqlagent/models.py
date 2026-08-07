"""Pydantic 数据模型。"""
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="整体状态: healthy / unhealthy")
    redis: bool = Field(description="Redis 连接状态")
    version: str = Field(description="应用版本")
