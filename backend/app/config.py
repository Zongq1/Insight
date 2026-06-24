"""Project Insight 配置管理模块

使用 Pydantic Settings 进行类型安全的配置管理。
所有配置项通过环境变量或 .env 文件加载。
"""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ===== Application =====
    APP_ENV: str = Field(default="development", description="运行环境: development/staging/production")
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    DEBUG: bool = Field(default=True, description="调试模式")

    # ===== LLM =====
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, description="OpenAI API Base URL (for compatible APIs)")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API Key")
    LLM_MODEL: str = Field(default="gpt-4o", description="默认 LLM 模型")
    LLM_MAX_RETRIES: int = Field(default=3, description="LLM 调用最大重试次数")

    # ===== Database =====
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://insight:insight123@localhost:5432/insight",
        description="PostgreSQL 连接 URL"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis 连接 URL")

    # ===== News API =====
    NEWS_API_KEY: Optional[str] = Field(default=None, description="News API Key")

    # ===== Cost Control =====
    DAILY_BUDGET_USD: float = Field(default=50.0, description="每日 Token 预算 (USD)")
    MONTHLY_BUDGET_USD: float = Field(default=1500.0, description="每月 Token 预算 (USD)")

    # ===== Vector Database =====
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_data",
        description="ChromaDB 持久化目录"
    )
    EMBEDDING_MODEL: str = Field(
        default="BAAI/bge-m3",
        description="Embedding 模型名称"
    )

    # ===== Scheduler =====
    SCHEDULER_ENABLED: bool = Field(default=True, description="是否启用定时调度")
    SCHEDULER_INTERVAL_MINUTES: int = Field(default=30, description="定时调度间隔（分钟）")
    NEWSNOW_PLATFORMS: str = Field(
        default="weibo,zhihu,toutiao",
        description="NewsNow 抓取平台列表（逗号分隔）"
    )

    # ===== CORS =====
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="允许的 CORS 来源"
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"APP_ENV must be one of {valid_envs}")
        return v


# 全局配置实例
settings = Settings()
