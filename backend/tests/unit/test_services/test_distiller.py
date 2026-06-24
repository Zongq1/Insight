"""DistillerNode 测试

测试提纯者节点的功能。
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import LLMError
from app.models.llm import FinalBriefing, LogicPoint, Source
from app.services.agents.distiller import DistillerNode, distiller_node


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


class TestDistillerNode:
    """DistillerNode 测试"""

    def test_init(self):
        """测试初始化"""
        node = DistillerNode()
        assert node.system_prompt is not None
        assert "冷酷客观" in node.system_prompt

    @pytest.mark.asyncio
    async def test_distill_success(self):
        """测试成功的文本提纯"""
        node = DistillerNode()
        mock_briefing = make_sample_briefing()

        with patch("app.services.agents.distiller.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_briefing)

            result = await node.distill(
                "这是一篇关于 AI 技术发展的长篇文章，包含大量数据分析和行业洞察。"
                "文章指出多家科技巨头在 2024 年大幅增加了 AI 研发投入。"
            )

            assert result is not None
            assert isinstance(result, FinalBriefing)
            assert result.category == "AI"
            assert result.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_distill_empty_text(self):
        """测试空文本"""
        node = DistillerNode()

        result = await node.distill("")
        assert result is None

    @pytest.mark.asyncio
    async def test_distill_short_text(self):
        """测试过短文本"""
        node = DistillerNode()

        result = await node.distill("短文本")
        assert result is None

    @pytest.mark.asyncio
    async def test_distill_llm_error(self):
        """测试 LLM 调用失败"""
        node = DistillerNode()

        with patch("app.services.agents.distiller.llm_client") as mock_client:
            mock_client.extract = AsyncMock(side_effect=LLMError("API Error"))

            result = await node.distill(
                "这是一篇足够长的测试文章，用于验证当 LLM 调用失败时的错误处理逻辑。"
                "文章包含足够的文本内容以通过长度检查。"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_distill_with_topic(self):
        """测试带主题的提纯"""
        node = DistillerNode()
        mock_briefing = make_sample_briefing()

        with patch("app.services.agents.distiller.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_briefing)

            result = await node.distill(
                "这是一篇关于 AI 技术发展的长篇文章，包含大量数据分析和行业洞察。"
                "文章指出多家科技巨头在 2024 年大幅增加了 AI 研发投入，推动了整个行业的变革。",
                topic="人工智能",
            )

            assert result is not None
            # 验证 topic 被传入了 prompt
            call_args = mock_client.extract.call_args
            messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
            user_msg = messages[1]["content"]
            assert "人工智能" in user_msg

    @pytest.mark.asyncio
    async def test_distill_batch(self):
        """测试批量提纯"""
        node = DistillerNode()
        mock_briefing = make_sample_briefing()

        texts = [
            "这是一篇关于 AI 技术发展的长篇文章，包含大量数据分析和行业洞察。"
            "文章指出多家科技巨头在 2024 年大幅增加了 AI 研发投入，推动了整个行业的变革。",
            "这是第二篇关于机器学习的深度分析文章，探讨了最新的技术趋势和应用场景。"
            "机器学习在自然语言处理和计算机视觉领域取得了突破性进展。",
        ]

        with patch("app.services.agents.distiller.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_briefing)

            results = await node.distill_batch(texts, topic="AI")

            assert len(results) == 2
            assert all(isinstance(r, FinalBriefing) for r in results)

    @pytest.mark.asyncio
    async def test_distill_batch_partial_failure(self):
        """测试批量提纯部分失败"""
        node = DistillerNode()
        mock_briefing = make_sample_briefing()

        texts = [
            "这是一篇关于 AI 技术发展的长篇文章，包含大量数据分析和行业洞察。"
            "文章指出多家科技巨头在 2024 年大幅增加了 AI 研发投入，推动了整个行业的变革。",
            "短",  # 太短，会失败
        ]

        with patch("app.services.agents.distiller.llm_client") as mock_client:
            mock_client.extract = AsyncMock(return_value=mock_briefing)

            results = await node.distill_batch(texts)

            # 只有第一篇成功
            assert len(results) == 1

    def test_build_user_prompt_with_topic(self):
        """测试构建带主题的用户提示"""
        node = DistillerNode()

        prompt = node._build_user_prompt("测试文本", "AI")

        assert "AI" in prompt
        assert "测试文本" in prompt
        assert "目标主题" in prompt

    def test_build_user_prompt_without_topic(self):
        """测试构建不带主题的用户提示"""
        node = DistillerNode()

        prompt = node._build_user_prompt("测试文本", "")

        assert "测试文本" in prompt
        assert "目标主题" not in prompt

    def test_build_user_prompt_truncation(self):
        """测试长文本截断"""
        node = DistillerNode()

        long_text = "x" * 60000
        prompt = node._build_user_prompt(long_text, "")

        assert len(prompt) <= 50100  # 50000 + 截断标记

    def test_global_instance(self):
        """测试全局实例"""
        assert distiller_node is not None
        assert isinstance(distiller_node, DistillerNode)
