"""Repository 基类

提供通用的 CRUD 操作。
"""

from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repository 基类

    提供通用的 CRUD 操作。
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        """创建记录

        Args:
            **kwargs: 模型字段

        Returns:
            创建的记录
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """根据 ID 获取记录

        Args:
            id: 记录 ID

        Returns:
            记录或 None
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """获取所有记录

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            记录列表
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, id: int, **kwargs: Any) -> Optional[ModelType]:
        """更新记录

        Args:
            id: 记录 ID
            **kwargs: 要更新的字段

        Returns:
            更新后的记录或 None
        """
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        """删除记录

        Args:
            id: 记录 ID

        Returns:
            是否成功删除
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def count(self) -> int:
        """统计记录数

        Returns:
            记录总数
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, id: int) -> bool:
        """检查记录是否存在

        Args:
            id: 记录 ID

        Returns:
            是否存在
        """
        from sqlalchemy import exists as sa_exists

        stmt = select(sa_exists().where(self.model.id == id))
        result = await self.session.execute(stmt)
        return result.scalar_one()
