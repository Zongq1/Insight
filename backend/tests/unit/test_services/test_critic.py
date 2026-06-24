"""CriticNode 测试

测试红队审稿人节点的功能。
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import LLMError
from app.models.llm import FinalBriefing, LogicPoint, Source
from app.services.agents.critic import CriticNode, CriticReview, critic_node


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


def make_sample_review(approved: bool = True, confidence: float = 0.85) -> CriticReview:
    """创建示例 CriticReview"""
    return CriticReview(
        is_approved=approved,
        confidence_score=confidence,
        feedback="逻辑严密，数据充分" if approved else "证据不足，逻辑跳跃",
        missing_evidence=[] if approved else ["缺少独立来源验证"],
        suggested_improvements=[] if approved else ["需要更多数据支撑"],
        logic_issues=[] if approved else ["前提和结论之间缺乏必然联系"],
    )


class TestCriticNode:
    """CriticNode 测试"""

    def test_init(self):
        """测试初始化"""
        node = CriticNode()
        assert node.system_prompt is not None
        assert "红队审稿人" in node.system_prompt
        assert node.approval_threshold == 0.7

    @pytest.mark.asyncio
    async def test_review_approved(self):
        """测试通过评审"""
        node = CriticNode()
        briefing = make_sample_briefing()
        mock_review = make_sample_review(approved=True, confidence=0.85)

        with patch("app.services.agents.critic.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_review)

            result = await node.review(briefing)

            assert result.is_approved is True
            assert result.confidence_score == 0.85
            assert "逻辑严密" in result.feedback

    @pytest.mark.asyncio
    async def test_review_rejected(self):
        """测试拒绝评审"""
        node = CriticNode()
        briefing = make_sample_briefing()
        mock_review = make_sample_review(approved=False, confidence=0.4)

        with patch("app.services.agents.critic.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_review)

            result = await node.review(briefing)

            assert result.is_approved is False
            assert result.confidence_score == 0.4
            assert len(result.missing_evidence) > 0

    @pytest.mark.asyncio
    async def test_review_threshold_boundary(self):
        """测试阈值边界"""
        node = CriticNode()

        # 刚好在阈值上
        briefing = make_sample_briefing()
        mock_review = CriticReview(
            is_approved=False,  # LLM 返回的 is_approved 会被覆盖
            confidence_score=0.7,
            feedback="边界情况",
        )

        with patch("app.services.agents.critic.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_review)

            result = await node.review(briefing)

            # 0.7 >= 0.7，应该通过
            assert result.is_approved is True

    @pytest.mark.asyncio
    async def test_review_below_threshold(self):
        """测试低于阈值"""
        node = CriticNode()

        briefing = make_sample_briefing()
        mock_review = CriticReview(
            is_approved=True,  # LLM 返回的 is_approved 会被覆盖
            confidence_score=0.69,
            feedback="略低于阈值",
        )

        with patch("app.services.agents.critic.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_review)

            result = await node.review(briefing)

            # 0.69 < 0.7，应该被拒绝
            assert result.is_approved is False

    @pytest.mark.asyncio
    async def test_review_llm_error(self):
        """测试 LLM 调用失败"""
        node = CriticNode()
        briefing = make_sample_briefing()

        with patch("app.services.agents.critic.llm_client") as mock_client:
            mock_client.extract = AsyncMock(side_effect=LLMError("API Error"))

            result = await node.review(briefing)

            # 错误时返回低置信度拒绝
            assert result.is_approved is False
            assert result.confidence_score == 0.0
            assert "出错" in result.feedback

    @pytest.mark.asyncio
    async def test_review_batch(self):
        """测试批量评审"""
        node = CriticNode()
        briefings = [make_sample_briefing() for _ in range(3)]
        mock_review = make_sample_review(approved=True, confidence=0.9)

        with patch("app.services.agents.critic.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_review)

            results = await node.review_batch(briefings)

            assert len(results) == 3
            assert all(r.is_approved for r in results)

    @pytest.mark.asyncio
    async def test_review_batch_mixed(self):
        """测试批量评审混合结果"""
        node = CriticNode()
        briefings = [make_sample_briefing() for _ in range(3)]

        reviews = [
            make_sample_review(approved=True, confidence=0.9),
            make_sample_review(approved=False, confidence=0.3),
            make_sample_review(approved=True, confidence=0.8),
        ]

        with patch("app.services.agents.critic.llm_client") as mock_client:
            mock_client.extract = AsyncMock(side_effect=reviews)

            results = await node.review_batch(briefings)

            assert len(results) == 3
            assert results[0].is_approved is True
            assert results[1].is_approved is False
            assert results[2].is_approved is True

    def test_build_review_prompt(self):
        """测试构建评审提示"""
        node = CriticNode()
        briefing = make_sample_briefing()

        prompt = node._build_review_prompt(briefing, "")

        assert "AI" in prompt
        assert "AI 技术正在加速渗透企业级应用" in prompt
        assert "逻辑推演链" in prompt
        assert "信息来源" in prompt

    def test_build_review_prompt_with_context(self):
        """测试带上下文的评审提示"""
        node = CriticNode()
        briefing = make_sample_briefing()

        prompt = node._build_review_prompt(briefing, "额外的上下文信息")

        assert "额外上下文" in prompt
        assert "额外的上下文信息" in prompt

    def test_build_review_prompt_with_historical(self):
        """测试带历史洞察的评审提示"""
        node = CriticNode()
        briefing = make_sample_briefing()
        briefing.historical_insight = "与历史趋势一致"

        prompt = node._build_review_prompt(briefing, "")

        assert "历史洞察" in prompt
        assert "与历史趋势一致" in prompt

    def test_global_instance(self):
        """测试全局实例"""
        assert critic_node is not None
        assert isinstance(critic_node, CriticNode)


class TestCriticReview:
    """CriticReview 模型测试"""

    def test_valid_review(self):
        """测试有效的评审结果"""
        review = CriticReview(
            is_approved=True,
            confidence_score=0.9,
            feedback="优秀",
        )
        assert review.is_approved is True
        assert review.confidence_score == 0.9

    def test_default_fields(self):
        """测试默认字段"""
        review = CriticReview(
            is_approved=False,
            confidence_score=0.5,
            feedback="一般",
        )
        assert review.missing_evidence == []
        assert review.suggested_improvements == []
        assert review.logic_issues == []

    def test_invalid_confidence_score(self):
        """测试无效的置信度分数"""
        with pytest.raises(Exception):
            CriticReview(
                is_approved=True,
                confidence_score=1.5,  # 超出范围
                feedback="测试",
            )

    def test_invalid_confidence_negative(self):
        """测试负置信度分数"""
        with pytest.raises(Exception):
            CriticReview(
                is_approved=True,
                confidence_score=-0.1,  # 负值
                feedback="测试",
            )
