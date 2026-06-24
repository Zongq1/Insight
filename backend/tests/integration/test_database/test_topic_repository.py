"""Topic Repository 测试"""

import pytest
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.db.base import Base
from app.models.db.topic import Topic
from app.repositories.topic import TopicRepository


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_sessionmaker(engine, class_=AsyncSession)() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def topic_repo(db_session):
    """创建 Topic Repository"""
    return TopicRepository(db_session)


class TestTopicRepository:
    """Topic Repository 测试"""

    @pytest.mark.asyncio
    async def test_create_topic(self, topic_repo):
        """测试创建主题"""
        topic = await topic_repo.create(
            name="AI Technology",
            keywords=["artificial intelligence", "machine learning"],
        )

        assert topic.id is not None
        assert topic.name == "AI Technology"
        assert len(topic.keywords) == 2

    @pytest.mark.asyncio
    async def test_get_by_id(self, topic_repo):
        """测试根据 ID 获取主题"""
        created = await topic_repo.create(
            name="Blockchain",
            keywords=["blockchain", "crypto"],
        )

        retrieved = await topic_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Blockchain"

    @pytest.mark.asyncio
    async def test_get_by_name(self, topic_repo):
        """测试根据名称获取主题"""
        await topic_repo.create(
            name="Python Programming",
            keywords=["python", "coding"],
        )

        result = await topic_repo.get_by_name("Python Programming")

        assert result is not None
        assert result.name == "Python Programming"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, topic_repo):
        """测试获取不存在的主题"""
        result = await topic_repo.get_by_name("NonExistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_unfetched(self, topic_repo):
        """测试获取未抓取的主题"""
        # 创建未抓取的主题
        await topic_repo.create(name="Topic1", keywords=["kw1"])
        await topic_repo.create(name="Topic2", keywords=["kw2"])

        # 创建已抓取的主题
        topic3 = await topic_repo.create(name="Topic3", keywords=["kw3"])
        await topic_repo.update(topic3.id, last_fetched_at=datetime.utcnow())

        unfetched = await topic_repo.get_unfetched()

        assert len(unfetched) == 2
        names = [t.name for t in unfetched]
        assert "Topic1" in names
        assert "Topic2" in names
        assert "Topic3" not in names

    @pytest.mark.asyncio
    async def test_get_stale(self, topic_repo):
        """测试获取需要更新的主题"""
        # 创建新主题（未抓取）
        await topic_repo.create(name="New", keywords=["new"])

        # 创建过期主题（25小时前抓取）
        old_time = datetime.utcnow() - timedelta(hours=25)
        topic_old = await topic_repo.create(name="Old", keywords=["old"])
        await topic_repo.update(topic_old.id, last_fetched_at=old_time)

        # 创建新鲜主题（1小时前抓取）
        fresh_time = datetime.utcnow() - timedelta(hours=1)
        topic_fresh = await topic_repo.create(name="Fresh", keywords=["fresh"])
        await topic_repo.update(topic_fresh.id, last_fetched_at=fresh_time)

        stale = await topic_repo.get_stale(hours=24)

        assert len(stale) == 2
        names = [t.name for t in stale]
        assert "New" in names
        assert "Old" in names
        assert "Fresh" not in names

    @pytest.mark.asyncio
    async def test_update_last_fetched(self, topic_repo):
        """测试更新最后抓取时间"""
        topic = await topic_repo.create(name="Test", keywords=["test"])

        assert topic.last_fetched_at is None

        updated = await topic_repo.update_last_fetched(topic.id)

        assert updated is not None
        assert updated.last_fetched_at is not None

    @pytest.mark.asyncio
    async def test_exists_by_name(self, topic_repo):
        """测试检查主题是否存在"""
        await topic_repo.create(name="Existing", keywords=["exist"])

        exists = await topic_repo.exists_by_name("Existing")
        not_exists = await topic_repo.exists_by_name("NotExisting")

        assert exists is True
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_delete_topic(self, topic_repo):
        """测试删除主题"""
        topic = await topic_repo.create(name="ToDelete", keywords=["delete"])

        deleted = await topic_repo.delete(topic.id)
        retrieved = await topic_repo.get_by_id(topic.id)

        assert deleted is True
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_count_topics(self, topic_repo):
        """测试统计主题数量"""
        count_before = await topic_repo.count()

        await topic_repo.create(name="Topic1", keywords=["kw1"])
        await topic_repo.create(name="Topic2", keywords=["kw2"])

        count_after = await topic_repo.count()

        assert count_before == 0
        assert count_after == 2

    @pytest.mark.asyncio
    async def test_get_all_topics(self, topic_repo):
        """测试获取所有主题"""
        await topic_repo.create(name="A", keywords=["a"])
        await topic_repo.create(name="B", keywords=["b"])
        await topic_repo.create(name="C", keywords=["c"])

        all_topics = await topic_repo.get_all()

        assert len(all_topics) == 3

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, topic_repo):
        """测试分页获取主题"""
        for i in range(5):
            await topic_repo.create(name=f"Topic{i}", keywords=[f"kw{i}"])

        page1 = await topic_repo.get_all(skip=0, limit=2)
        page2 = await topic_repo.get_all(skip=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_update_topic(self, topic_repo):
        """测试更新主题"""
        topic = await topic_repo.create(name="Original", keywords=["original"])

        updated = await topic_repo.update(topic.id, name="Updated", keywords=["updated"])

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.keywords == ["updated"]
