"""Pytest 配置文件

定义测试所需的 fixtures 和配置。
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """同步测试客户端"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# TODO: 添加数据库 fixtures
# @pytest.fixture
# async def db_session() -> AsyncGenerator[AsyncSession, None]:
#     """测试数据库会话"""
#     ...

# TODO: 添加 Redis fixtures
# @pytest.fixture
# async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
#     """测试 Redis 客户端"""
#     ...
