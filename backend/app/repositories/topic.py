"""Topic Repository

提供主题相关的数据访问操作。
"""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.topic import Topic
from app.repositories.base import BaseRepository


class TopicRepository(BaseRepository[Topic]):
    """Topic Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(Topic, session)

    async def get_by_name(self, name: str) -> Optional[Topic]:
        """根据名称获取主题

        Args:
            name: 主题名称

        Returns:
            主题或 None
        """
        stmt = select(Topic).where(Topic.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_keyword(self, keyword: str) -> Sequence[Topic]:
        """根据关键词获取主题

        Args:
            keyword: 关键词

        Returns:
            主题列表
        """
        # 使用 JSON 包含查询
        stmt = select(Topic).where(Topic.keywords.contains(keyword))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_unfetched(
        self,
        limit: int = 10,
    ) -> Sequence[Topic]:
        """获取未抓取的主题

        Args:
            limit: 返回的最大记录数

        Returns:
            主题列表
        """
        stmt = (
            select(Topic)
            .where(Topic.last_fetched_at.is_(None))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_stale(
        self,
        hours: int = 24,
        limit: int = 10,
    ) -> Sequence[Topic]:
        """获取需要更新的主题

        Args:
            hours: 过期时间（小时）
            limit: 返回的最大记录数

        Returns:
            主题列表
        """
        from datetime import timedelta

        threshold = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(Topic)
            .where(
                (Topic.last_fetched_at.is_(None)) |
                (Topic.last_fetched_at < threshold)
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_last_fetched(self, topic_id: int) -> Optional[Topic]:
        """更新主题的最后抓取时间

        Args:
            topic_id: 主题 ID

        Returns:
            更新后的主题或 None
        """
        return await self.update(topic_id, last_fetched_at=datetime.utcnow())

    async def exists_by_name(self, name: str) -> bool:
        """检查主题是否存在

        Args:
            name: 主题名称

        Returns:
            是否存在
        """
        from sqlalchemy import exists as sa_exists

        stmt = select(sa_exists().where(Topic.name == name))
        result = await self.session.execute(stmt)
        return result.scalar_one()
