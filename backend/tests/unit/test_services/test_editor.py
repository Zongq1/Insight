"""MemoryEditorNode 测试

测试主编与记忆映射节点的功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import VectorDatabaseError
from app.models.llm import FinalBriefing, LogicPoint, Source
from app.services.agents.editor import HistoricalInsight, MemoryEditorNode, memory_editor_node
from app.services.vector.base import SearchResult, VectorDocument


def make_sample_briefing() -> FinalBriefing:
    """创建示例 FinalBriefing"""
    return FinalBriefing(
        category="AI",
        core_thesis="AI 技术正在加速渗透企业级应用",
        logic_chain=[
            LogicPoint(
                premise="多家科技巨头在 2024 年大幅增加 AI 研发投入",
                conclusion="AI 技术已从实验阶段进入大规模部署阶段",
            ),
            LogicPoint(
                premise="企业 AI 采用率同比增长 40%",
                conclusion="AI 正在从辅助工具转变为核心生产力",
            ),
        ],
        sources=[
            Source(name="TechCrunch", url="https://techcrunch.com/ai-2024"),
        ],
        confidence_score=0.85,
    )


def make_search_result(score: float = 0.9) -> SearchResult:
    """创建示例 SearchResult"""
    return SearchResult(
        document=VectorDocument(
            id="test_doc_1",
            content="历史洞见内容",
            metadata={"category": "AI", "date_generated": "2024-01-01"},
        ),
        score=score,
    )


class TestMemoryEditorNode:
    """MemoryEditorNode 测试"""

    def test_init(self):
        """测试初始化"""
        node = MemoryEditorNode()
        assert node.vector_store is not None
        assert node.SIMILARITY_THRESHOLD == 0.82

    @pytest.mark.asyncio
    async def test_process_insight_success(self):
        """测试成功的洞见处理"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        mock_vector_store = AsyncMock()
        mock_vector_store.search = AsyncMock(return_value=[])
        mock_vector_store.add_document = AsyncMock()

        node.vector_store = mock_vector_store

        result = await node.process_insight(briefing, topic="AI")

        assert isinstance(result, FinalBriefing)
        mock_vector_store.add_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_insight_with_similar(self):
        """测试发现相似历史洞见"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        mock_vector_store = AsyncMock()
        mock_vector_store.search = AsyncMock(
            return_value=[make_search_result(score=0.92)]
        )
        mock_vector_store.add_document = AsyncMock()

        node.vector_store = mock_vector_store

        result = await node.process_insight(briefing, topic="AI")

        assert result.historical_insight is not None
        # 验证包含相似度分数
        assert "92%" in result.historical_insight

    @pytest.mark.asyncio
    async def test_process_insight_progressive(self):
        """测试递进发展关系"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        mock_vector_store = AsyncMock()
        mock_vector_store.search = AsyncMock(
            return_value=[make_search_result(score=0.86)]
        )
        mock_vector_store.add_document = AsyncMock()

        node.vector_store = mock_vector_store

        result = await node.process_insight(briefing, topic="AI")

        assert result.historical_insight is not None
        # 验证包含相似度分数
        assert "86%" in result.historical_insight

    @pytest.mark.asyncio
    async def test_process_insight_related(self):
        """测试相关关联关系"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        mock_vector_store = AsyncMock()
        mock_vector_store.search = AsyncMock(
            return_value=[make_search_result(score=0.83)]
        )
        mock_vector_store.add_document = AsyncMock()

        node.vector_store = mock_vector_store

        result = await node.process_insight(briefing, topic="AI")

        assert result.historical_insight is not None
        # 验证包含相似度分数
        assert "83%" in result.historical_insight

    @pytest.mark.asyncio
    async def test_process_insight_vector_error(self):
        """测试向量数据库错误"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        mock_vector_store = AsyncMock()
        mock_vector_store.search = AsyncMock(
            side_effect=VectorDatabaseError("DB Error")
        )
        mock_vector_store.add_document = AsyncMock()

        node.vector_store = mock_vector_store

        result = await node.process_insight(briefing, topic="AI")

        # 向量数据库错误不影响洞见返回
        assert isinstance(result, FinalBriefing)
        assert result.historical_insight is None

    @pytest.mark.asyncio
    async def test_process_batch(self):
        """测试批量处理"""
        node = MemoryEditorNode()
        briefings = [make_sample_briefing() for _ in range(3)]

        mock_vector_store = AsyncMock()
        mock_vector_store.search = AsyncMock(return_value=[])
        mock_vector_store.add_document = AsyncMock()

        node.vector_store = mock_vector_store

        results = await node.process_batch(briefings, topic="AI")

        assert len(results) == 3
        assert all(isinstance(r, FinalBriefing) for r in results)

    def test_prepare_text_for_embedding(self):
        """测试嵌入文本准备"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        text = node._prepare_text_for_embedding(briefing)

        assert "AI" in text
        assert "AI 技术正在加速渗透企业级应用" in text
        assert "多家科技巨头" in text

    def test_embedding_service_available(self):
        """测试嵌入服务可用"""
        node = MemoryEditorNode()
        service = node.embedding_service
        assert service is not None
        assert service.dimension > 0

    def test_embedding_service_embed(self):
        """测试嵌入服务生成向量"""
        node = MemoryEditorNode()
        embedding = node.embedding_service.embed("测试文本")

        assert len(embedding) == node.embedding_service.dimension
        assert all(0.0 <= v <= 1.0 for v in embedding)

    def test_embedding_service_deterministic(self):
        """测试嵌入服务确定性"""
        node = MemoryEditorNode()

        emb1 = node.embedding_service.embed("相同文本")
        emb2 = node.embedding_service.embed("相同文本")

        assert emb1 == emb2

    def test_embedding_service_different_text(self):
        """测试不同文本生成不同向量"""
        node = MemoryEditorNode()

        emb1 = node.embedding_service.embed("文本A")
        emb2 = node.embedding_service.embed("文本B")

        assert emb1 != emb2

    def test_generate_historical_insight_high_similarity(self):
        """测试高相似度历史洞察"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        similar = [make_search_result(score=0.95)]
        result = node._generate_historical_insight(briefing, similar)

        assert result is not None
        assert "95%" in result

    def test_generate_historical_insight_no_similar(self):
        """测试无相似洞见"""
        node = MemoryEditorNode()
        briefing = make_sample_briefing()

        result = node._generate_historical_insight(briefing, [])

        assert result is None

    def test_global_instance(self):
        """测试全局实例"""
        assert memory_editor_node is not None
        assert isinstance(memory_editor_node, MemoryEditorNode)


class TestHistoricalInsight:
    """HistoricalInsight 模型测试"""

    def test_creation(self):
        """测试创建"""
        insight = HistoricalInsight(
            insight_id="test_1",
            content="测试内容",
            score=0.9,
            relationship="高度一致",
        )
        assert insight.insight_id == "test_1"
        assert insight.score == 0.9
