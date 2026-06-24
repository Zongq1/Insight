"""Insight Repository 测试"""

import pytest
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.db.base import Base
from app.models.db.insight import Insight
from app.repositories.insight import InsightRepository


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
def insight_repo(db_session):
    """创建 Insight Repository"""
    return InsightRepository(db_session)


class TestInsightRepository:
    """Insight Repository 测试"""

    @pytest.mark.asyncio
    async def test_create_insight(self, insight_repo):
        """测试创建洞见"""
        insight = await insight_repo.create(
            category="AI",
            core_thesis="AI 技术正在快速发展",
            logic_chain=[
                {"premise": "前提1", "conclusion": "结论1"},
                {"premise": "前提2", "conclusion": "结论2"},
            ],
            sources=[
                {"name": "Test", "url": "https://example.com"},
            ],
            confidence_score=0.8,
            date_generated=date.today(),
        )

        assert insight.id is not None
        assert insight.category == "AI"
        assert insight.core_thesis == "AI 技术正在快速发展"
        assert insight.confidence_score == 0.8

    @pytest.mark.asyncio
    async def test_get_by_id(self, insight_repo):
        """测试根据 ID 获取洞见"""
        # 创建洞见
        created = await insight_repo.create(
            category="AI",
            core_thesis="测试洞见",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )

        # 获取洞见
        retrieved = await insight_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.core_thesis == "测试洞见"

    @pytest.mark.asyncio
    async def test_get_by_date(self, insight_repo):
        """测试按日期获取洞见"""
        today = date.today()

        # 创建多个洞见
        await insight_repo.create(
            category="AI",
            core_thesis="今日洞见1",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=today,
        )
        await insight_repo.create(
            category="Blockchain",
            core_thesis="今日洞见2",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=today,
        )

        # 按日期查询
        insights = await insight_repo.get_by_date(today)

        assert len(insights) == 2

    @pytest.mark.asyncio
    async def test_get_by_category(self, insight_repo):
        """测试按分类获取洞见"""
        await insight_repo.create(
            category="AI",
            core_thesis="AI 洞见",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )
        await insight_repo.create(
            category="Blockchain",
            core_thesis="区块链洞见",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )

        # 按分类查询
        ai_insights = await insight_repo.get_by_category("AI")
        assert len(ai_insights) == 1
        assert ai_insights[0].category == "AI"

    @pytest.mark.asyncio
    async def test_get_high_confidence(self, insight_repo):
        """测试获取高置信度洞见"""
        await insight_repo.create(
            category="AI",
            core_thesis="高置信度洞见",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            confidence_score=0.9,
            date_generated=date.today(),
        )
        await insight_repo.create(
            category="AI",
            core_thesis="低置信度洞见",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            confidence_score=0.3,
            date_generated=date.today(),
        )

        # 获取高置信度洞见
        high_confidence = await insight_repo.get_high_confidence(min_confidence=0.7)
        assert len(high_confidence) == 1
        assert high_confidence[0].confidence_score >= 0.7

    @pytest.mark.asyncio
    async def test_update_insight(self, insight_repo):
        """测试更新洞见"""
        created = await insight_repo.create(
            category="AI",
            core_thesis="原始内容",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )

        # 更新洞见
        updated = await insight_repo.update(
            created.id,
            core_thesis="更新后的内容",
            confidence_score=0.95,
        )

        assert updated is not None
        assert updated.core_thesis == "更新后的内容"
        assert updated.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_delete_insight(self, insight_repo):
        """测试删除洞见"""
        created = await insight_repo.create(
            category="AI",
            core_thesis="待删除洞见",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )

        # 删除洞见
        deleted = await insight_repo.delete(created.id)
        assert deleted is True

        # 验证已删除
        retrieved = await insight_repo.get_by_id(created.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_count(self, insight_repo):
        """测试统计洞见数量"""
        # 初始数量为 0
        count = await insight_repo.count()
        assert count == 0

        # 创建洞见
        await insight_repo.create(
            category="AI",
            core_thesis="洞见1",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )
        await insight_repo.create(
            category="AI",
            core_thesis="洞见2",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )

        # 验证数量
        count = await insight_repo.count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_search_by_thesis(self, insight_repo):
        """测试按关键词搜索洞见"""
        await insight_repo.create(
            category="AI",
            core_thesis="人工智能技术正在快速发展",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )
        await insight_repo.create(
            category="Blockchain",
            core_thesis="区块链技术改变了金融行业",
            logic_chain=[{"premise": "前提", "conclusion": "结论"}],
            sources=[{"name": "Test", "url": "https://example.com"}],
            date_generated=date.today(),
        )

        # 搜索包含"人工智能"的洞见
        results = await insight_repo.search_by_thesis("人工智能")
        assert len(results) == 1
        assert "人工智能" in results[0].core_thesis
