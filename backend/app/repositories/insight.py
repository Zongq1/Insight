"""Insight Repository

提供洞见相关的数据访问操作。
"""

from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.insight import Insight
from app.repositories.base import BaseRepository


class InsightRepository(BaseRepository[Insight]):
    """Insight Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(Insight, session)

    async def get_by_date(
        self,
        target_date: date,
        skip: int = 0,
        limit: int = 10,
    ) -> Sequence[Insight]:
        """按日期获取洞见

        Args:
            target_date: 目标日期
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            洞见列表
        """
        stmt = (
            select(Insight)
            .where(Insight.date_generated == target_date)
            .order_by(Insight.confidence_score.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 10,
    ) -> Sequence[Insight]:
        """按分类获取洞见

        Args:
            category: 分类标签
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            洞见列表
        """
        stmt = (
            select(Insight)
            .where(Insight.category == category)
            .order_by(Insight.date_generated.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_high_confidence(
        self,
        min_confidence: float = 0.7,
        skip: int = 0,
        limit: int = 10,
    ) -> Sequence[Insight]:
        """获取高置信度洞见

        Args:
            min_confidence: 最低置信度阈值
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            洞见列表
        """
        stmt = (
            select(Insight)
            .where(Insight.confidence_score >= min_confidence)
            .order_by(Insight.confidence_score.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest(
        self,
        limit: int = 10,
    ) -> Sequence[Insight]:
        """获取最新洞见

        Args:
            limit: 返回的最大记录数

        Returns:
            洞见列表
        """
        stmt = (
            select(Insight)
            .order_by(Insight.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_by_thesis(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 10,
    ) -> Sequence[Insight]:
        """按关键词搜索洞见

        Args:
            keyword: 搜索关键词
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            洞见列表
        """
        stmt = (
            select(Insight)
            .where(Insight.core_thesis.ilike(f"%{keyword}%"))
            .order_by(Insight.date_generated.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_date(self, target_date: date) -> int:
        """统计指定日期的洞见数量

        Args:
            target_date: 目标日期

        Returns:
            洞见数量
        """
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(Insight)
            .where(Insight.date_generated == target_date)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_by_category(self, category: str) -> int:
        """统计指定分类的洞见数量

        Args:
            category: 分类标签

        Returns:
            洞见数量
        """
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(Insight)
            .where(Insight.category == category)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
