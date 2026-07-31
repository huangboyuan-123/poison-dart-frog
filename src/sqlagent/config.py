"""
配置管理模块 - 从环境变量加载应用配置。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
_env_file = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_file)


@dataclass
class LLMConfig:
    """LLM API 配置"""

    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))


@dataclass
class DatabaseConfig:
    """数据库连接配置"""

    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///sqlagent.db"))


@dataclass
class AppConfig:
    """应用配置"""

    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    read_only: bool = field(default_factory=lambda: os.getenv("READ_ONLY", "true").lower() == "true")


# 全局配置单例
config = AppConfig()
