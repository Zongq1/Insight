"""Alembic 环境配置

用于数据库迁移。
"""

import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.models.db.base import Base

# 导入所有 ORM 模型，确保 Alembic 能检测到
from app.models.db.insight import Insight, InsightVersion
from app.models.db.token_usage import TokenUsageRecord
from app.models.db.topic import Topic, TopicInsight

# Alembic Config 对象
config = context.config

# 设置数据库 URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置 MetaData
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """运行离线迁移

    生成 SQL 脚本而不连接数据库。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """运行异步迁移

    连接数据库并执行迁移。
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """运行在线迁移"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
