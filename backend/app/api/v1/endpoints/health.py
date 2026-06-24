"""健康检查 API 端点"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class HealthStatus(BaseModel):
    """健康状态响应模型"""

    status: str = "ok"
    timestamp: datetime
    version: str = "0.1.0"
    environment: str
    checks: dict[str, str] = {}


class HealthChecker:
    """健康检查器"""

    async def check_database(self) -> str:
        """检查数据库连接"""
        # TODO: 实现实际的数据库连接检查
        # async with async_session() as session:
        #     await session.execute(text("SELECT 1"))
        return "ok"

    async def check_redis(self) -> str:
        """检查 Redis 连接"""
        # TODO: 实现实际的 Redis 连接检查
        # redis = aioredis.from_url(settings.REDIS_URL)
        # await redis.ping()
        return "ok"

    async def check_llm(self) -> str:
        """检查 LLM 服务可用性"""
        # 注意: 不应在健康检查中实际调用 LLM，这会产生费用
        # 只检查 API Key 是否配置
        return "configured"


health_checker = HealthChecker()


@router.get("", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """基础健康检查

    返回服务基本状态，不检查外部依赖。
    """
    from app.config import settings

    return HealthStatus(
        status="ok",
        timestamp=datetime.now(),
        environment=settings.APP_ENV,
    )


@router.get("/detailed", response_model=HealthStatus)
async def detailed_health_check() -> HealthStatus:
    """详细健康检查

    检查所有外部依赖的连接状态。
    """
    from app.config import settings

    checks = {
        "database": await health_checker.check_database(),
        "redis": await health_checker.check_redis(),
        "llm": await health_checker.check_llm(),
    }

    # 如果任何检查失败，状态为 degraded
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    return HealthStatus(
        status=status,
        timestamp=datetime.now(),
        environment=settings.APP_ENV,
        checks=checks,
    )
