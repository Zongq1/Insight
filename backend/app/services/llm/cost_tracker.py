"""Token 成本追踪器

监控和控制 LLM API 调用的成本。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import CostLimitExceededError

logger = logging.getLogger(__name__)


# GPT-4o 定价 (2024年)
MODEL_PRICING = {
    "gpt-4o": {
        "input": 2.50 / 1_000_000,   # $2.50 per 1M input tokens
        "output": 10.00 / 1_000_000,  # $10.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,   # $0.15 per 1M input tokens
        "output": 0.60 / 1_000_000,  # $0.60 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input": 10.00 / 1_000_000,  # $10.00 per 1M input tokens
        "output": 30.00 / 1_000_000, # $30.00 per 1M output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.50 / 1_000_000,   # $0.50 per 1M input tokens
        "output": 1.50 / 1_000_000,  # $1.50 per 1M output tokens
    },
    "claude-3-opus": {
        "input": 15.00 / 1_000_000,  # $15.00 per 1M input tokens
        "output": 75.00 / 1_000_000, # $75.00 per 1M output tokens
    },
    "claude-3-sonnet": {
        "input": 3.00 / 1_000_000,   # $3.00 per 1M input tokens
        "output": 15.00 / 1_000_000, # $15.00 per 1M output tokens
    },
    "claude-3-haiku": {
        "input": 0.25 / 1_000_000,   # $0.25 per 1M input tokens
        "output": 1.25 / 1_000_000,  # $1.25 per 1M output tokens
    },
}


class TokenUsage(BaseModel):
    """Token 使用记录"""

    model: str = Field(..., description="模型名称")
    input_tokens: int = Field(..., ge=0, description="输入 Token 数量")
    output_tokens: int = Field(..., ge=0, description="输出 Token 数量")
    input_cost: float = Field(..., ge=0, description="输入成本 (USD)")
    output_cost: float = Field(..., ge=0, description="输出成本 (USD)")
    total_cost: float = Field(..., ge=0, description="总成本 (USD)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict, description="额外元数据")


class CostSummary(BaseModel):
    """成本汇总"""

    daily_cost: float = Field(default=0.0, description="当日累计成本")
    monthly_cost: float = Field(default=0.0, description="当月累计成本")
    daily_budget: float = Field(default=settings.DAILY_BUDGET_USD, description="每日预算")
    monthly_budget: float = Field(default=settings.MONTHLY_BUDGET_USD, description="每月预算")
    daily_remaining: float = Field(default=0.0, description="当日剩余预算")
    monthly_remaining: float = Field(default=0.0, description="当月剩余预算")
    daily_usage_count: int = Field(default=0, description="当日调用次数")
    monthly_usage_count: int = Field(default=0, description="当月调用次数")


class CostTracker:
    """成本追踪器

    追踪 LLM API 调用的成本，并提供预算控制功能。
    """

    def __init__(self):
        # 内存缓存，实际应该使用 Redis
        self._daily_usage: list[TokenUsage] = []
        self._monthly_usage: list[TokenUsage] = []

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> tuple[float, float, float]:
        """计算 Token 成本

        Args:
            model: 模型名称
            input_tokens: 输入 Token 数量
            output_tokens: 输出 Token 数量

        Returns:
            (input_cost, output_cost, total_cost) 元组
        """
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            logger.warning(f"Unknown model pricing: {model}, using gpt-4o pricing")
            pricing = MODEL_PRICING["gpt-4o"]

        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        total_cost = input_cost + output_cost

        return input_cost, output_cost, total_cost

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[dict] = None,
    ) -> TokenUsage:
        """记录 Token 使用

        Args:
            model: 模型名称
            input_tokens: 输入 Token 数量
            output_tokens: 输出 Token 数量
            metadata: 额外元数据

        Returns:
            TokenUsage 记录
        """
        input_cost, output_cost, total_cost = self.calculate_cost(
            model, input_tokens, output_tokens
        )

        usage = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            metadata=metadata or {},
        )

        # 添加到内存缓存
        self._daily_usage.append(usage)
        self._monthly_usage.append(usage)

        logger.info(
            f"Token usage recorded: model={model}, "
            f"input={input_tokens}, output={output_tokens}, "
            f"cost=${total_cost:.4f}"
        )

        return usage

    def check_budget(self) -> CostSummary:
        """检查预算状态

        Returns:
            成本汇总信息
        """
        now = datetime.now(timezone.utc)

        # 计算当日成本
        daily_cost = sum(
            u.total_cost
            for u in self._daily_usage
            if u.timestamp.date() == now.date()
        )

        # 计算当月成本
        monthly_cost = sum(
            u.total_cost
            for u in self._monthly_usage
            if u.timestamp.year == now.year and u.timestamp.month == now.month
        )

        # 计算当日调用次数
        daily_count = sum(
            1
            for u in self._daily_usage
            if u.timestamp.date() == now.date()
        )

        # 计算当月调用次数
        monthly_count = sum(
            1
            for u in self._monthly_usage
            if u.timestamp.year == now.year and u.timestamp.month == now.month
        )

        summary = CostSummary(
            daily_cost=daily_cost,
            monthly_cost=monthly_cost,
            daily_remaining=max(0, settings.DAILY_BUDGET_USD - daily_cost),
            monthly_remaining=max(0, settings.MONTHLY_BUDGET_USD - monthly_cost),
            daily_usage_count=daily_count,
            monthly_usage_count=monthly_count,
        )

        return summary

    def validate_budget(self) -> None:
        """验证预算是否超限

        Raises:
            CostLimitExceededError: 预算超限
        """
        summary = self.check_budget()

        if summary.daily_cost >= settings.DAILY_BUDGET_USD:
            raise CostLimitExceededError(
                message="Daily budget exceeded",
                current_cost=summary.daily_cost,
                limit=settings.DAILY_BUDGET_USD,
            )

        if summary.monthly_cost >= settings.MONTHLY_BUDGET_USD:
            raise CostLimitExceededError(
                message="Monthly budget exceeded",
                current_cost=summary.monthly_cost,
                limit=settings.MONTHLY_BUDGET_USD,
            )

        # 接近阈值时记录警告
        daily_threshold = settings.DAILY_BUDGET_USD * 0.8
        if summary.daily_cost >= daily_threshold:
            logger.warning(
                f"Approaching daily budget limit: "
                f"${summary.daily_cost:.2f} / ${settings.DAILY_BUDGET_USD:.2f} "
                f"({summary.daily_cost / settings.DAILY_BUDGET_USD * 100:.1f}%)"
            )

        monthly_threshold = settings.MONTHLY_BUDGET_USD * 0.8
        if summary.monthly_cost >= monthly_threshold:
            logger.warning(
                f"Approaching monthly budget limit: "
                f"${summary.monthly_cost:.2f} / ${settings.MONTHLY_BUDGET_USD:.2f} "
                f"({summary.monthly_cost / settings.MONTHLY_BUDGET_USD * 100:.1f}%)"
            )

    async def persist_to_database(self) -> int:
        """持久化到数据库

        将内存中的使用记录写入 PostgreSQL。
        Returns:
            写入记录数量
        """
        from app.models.db.base import get_session_factory
        from app.models.db.token_usage import TokenUsageRecord

        if not self._daily_usage:
            return 0

        session_factory = get_session_factory()
        count = 0
        async with session_factory() as session:
            try:
                for usage in self._daily_usage:
                    record = TokenUsageRecord(
                        model=usage.model,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        input_cost=usage.input_cost,
                        output_cost=usage.output_cost,
                        total_cost=usage.total_cost,
                        metadata_json=json.dumps(usage.metadata) if usage.metadata else None,
                        recorded_at=usage.timestamp,
                    )
                    session.add(record)
                    count += 1
                await session.commit()
                logger.info(f"Persisted {count} token usage records to database")
            except Exception:
                await session.rollback()
                logger.exception("Failed to persist token usage to database")
                raise
        return count

    async def persist_to_redis(self) -> None:
        """持久化到 Redis

        将当日成本写入 Redis，用于快速查询。
        """
        try:
            import redis.asyncio as aioredis

            summary = self.check_budget()
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.set(
                f"cost:daily:{datetime.now(timezone.utc).date()}",
                summary.model_dump_json(),
                ex=86400,
            )
            await client.aclose()
            logger.info(f"Persisted daily cost ${summary.daily_cost:.4f} to Redis")
        except Exception:
            logger.exception("Failed to persist cost to Redis")


# 全局成本追踪器实例
cost_tracker = CostTracker()
