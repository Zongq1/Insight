"""SQLAlchemy 基础配置

定义异步数据库引擎、会话工厂和 ORM 基类。
"""

from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings

# 延迟初始化的全局变量
_engine = None
_async_session_factory = None


def get_engine():
    """获取或创建数据库引擎（延迟初始化）"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory():
    """获取或创建会话工厂（延迟初始化）"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


class Base(DeclarativeBase):
    """ORM 基类"""

    pass


class TimestampMixin:
    """时间戳混入类"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话

    用于 FastAPI 依赖注入。
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库

    创建所有表结构（仅用于开发环境）。
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    global _engine, _async_session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
