"""
配置管理模块 — 从环境变量加载 MySQL + LLM 配置。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录 .env 文件
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)


@dataclass
class MySQLConfig:
    """MySQL 数据库配置。"""

    host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "mysql"))
    port: int = field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", "root123"))
    database: str = field(default_factory=lambda: os.getenv("MYSQL_DATABASE", "sqlagent"))

    @property
    def url(self) -> str:
        """构建 SQLAlchemy 数据库连接 URL。"""
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset=utf8mb4"
        )


@dataclass
class LLMConfig:
    """LLM API 配置（OpenAI 兼容接口，默认使用 DeepSeek）。

    支持所有 OpenAI 兼容的 API 提供商：DeepSeek、OpenAI、Ollama 等。
    API Key 优先级: DEEPSEEK_API_KEY > OPENAI_API_KEY
    """

    api_key: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("OPENAI_API_KEY", "")
    )
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "LLM_BASE_URL", "https://api.deepseek.com/v1"
        )
    )
    model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "deepseek-chat")
    )


@dataclass
class AppConfig:
    """应用全局配置。"""

    mysql: MySQLConfig = field(default_factory=MySQLConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    read_only: bool = field(
        default_factory=lambda: os.getenv("READ_ONLY", "true").lower() == "true"
    )
    max_history: int = field(
        default_factory=lambda: int(os.getenv("MAX_HISTORY", "100"))
    )


# 全局配置单例
config = AppConfig()
