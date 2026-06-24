"""InsightWorkflow 集成测试

测试完整的多智能体协同工作流。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.llm import FinalBriefing, LogicPoint, Source
from app.services.agents.critic import CriticReview
from app.services.agents.workflow import InsightWorkflow, MAX_RETRY_COUNT


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


def make_approved_review() -> CriticReview:
    """创建通过的评审"""
    return CriticReview(
        is_approved=True,
        confidence_score=0.9,
        feedback="逻辑严密，数据充分",
    )


def make_rejected_review() -> CriticReview:
    """创建拒绝的评审"""
    return CriticReview(
        is_approved=False,
        confidence_score=0.3,
        feedback="证据不足，逻辑跳跃严重",
        missing_evidence=["缺少独立来源验证"],
        logic_issues=["前提和结论之间缺乏必然联系"],
    )


class TestInsightWorkflow:
    """InsightWorkflow 集成测试"""

    def test_init(self):
        """测试工作流初始化"""
        workflow = InsightWorkflow()
        assert workflow.graph is not None
        assert workflow.max_retry == MAX_RETRY_COUNT

    @pytest.mark.asyncio
    async def test_run_with_raw_texts_approved(self):
        """测试使用预置文本的完整流程（通过评审）"""
        workflow = InsightWorkflow()
        mock_briefing = make_sample_briefing()
        mock_review = make_approved_review()

        with (
            patch("app.services.agents.workflow.distiller_node") as mock_distiller,
            patch("app.services.agents.workflow.critic_node") as mock_critic,
            patch("app.services.agents.workflow.memory_editor_node") as mock_editor,
        ):
            # Mock Distiller
            mock_distiller.distill_batch = AsyncMock(return_value=[mock_briefing])

            # Mock Critic - 通过
            mock_critic.review_batch = AsyncMock(return_value=[mock_review])

            # Mock Editor
            processed_briefing = mock_briefing.model_copy()
            processed_briefing.historical_insight = "与历史趋势一致"
            mock_editor.process_batch = AsyncMock(return_value=[processed_briefing])

            # 创建自定义工作流
            workflow = InsightWorkflow(
                distiller=mock_distiller,
                critic=mock_critic,
                editor=mock_editor,
            )

            result = await workflow.run(
                topic="AI",
                raw_texts=["这是一篇关于 AI 技术发展的长篇文章，包含大量数据分析和行业洞察。文章内容丰富。"],
            )

            # 验证结果
            assert len(result.get("final_briefings", [])) == 1
            assert result.get("retry_count", 0) >= 1

            # 验证调用
            mock_distiller.distill_batch.assert_called_once()
            mock_critic.review_batch.assert_called_once()
            mock_editor.process_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_raw_texts_rejected(self):
        """测试使用预置文本的流程（评审拒绝，超过重试次数）"""
        workflow = InsightWorkflow()
        mock_briefing = make_sample_briefing()
        mock_review = make_rejected_review()

        with (
            patch("app.services.agents.workflow.distiller_node") as mock_distiller,
            patch("app.services.agents.workflow.critic_node") as mock_critic,
            patch("app.services.agents.workflow.memory_editor_node") as mock_editor,
        ):
            # Mock Distiller
            mock_distiller.distill_batch = AsyncMock(return_value=[mock_briefing])

            # Mock Critic - 拒绝
            mock_critic.review_batch = AsyncMock(return_value=[mock_review])

            # Mock Editor
            mock_editor.process_batch = AsyncMock(return_value=[])

            # 创建自定义工作流，最大重试 2 次
            workflow = InsightWorkflow(
                distiller=mock_distiller,
                critic=mock_critic,
                editor=mock_editor,
                max_retry=2,
            )

            result = await workflow.run(
                topic="AI",
                raw_texts=["这是一篇关于 AI 技术发展的长篇文章，包含大量数据分析和行业洞察。文章内容丰富。"],
            )

            # 验证重试次数
            assert result.get("retry_count", 0) >= 2
            # 最终没有通过的洞见
            assert len(result.get("final_briefings", [])) == 0

            # Distiller 应该被调用多次（重试）
            assert mock_distiller.distill_batch.call_count >= 2

    @pytest.mark.asyncio
    async def test_run_with_empty_texts(self):
        """测试空文本 - Scout 搜索无结果"""
        with patch("app.services.agents.workflow.scout_node") as mock_scout:
            mock_scout.generate_search_keywords = MagicMock(return_value=["AI", "AI 2024"])
            mock_scout.search_topic = AsyncMock(
                return_value=MagicMock(raw_texts=[])
            )

            workflow = InsightWorkflow(scout=mock_scout)
            result = await workflow.run(topic="AI", raw_texts=[])

            # 空文本应该导致空结果或错误
            assert (
                len(result.get("errors", [])) > 0
                or len(result.get("raw_texts", [])) == 0
                or len(result.get("draft_insights", [])) == 0
            )

    @pytest.mark.asyncio
    async def test_run_without_topic(self):
        """测试无主题"""
        with patch("app.services.agents.workflow.scout_node") as mock_scout:
            mock_scout.generate_search_keywords = MagicMock(return_value=[])

            workflow = InsightWorkflow(scout=mock_scout)
            result = await workflow.run(topic="", raw_texts=[])

            # 应该有错误或空结果
            assert (
                len(result.get("errors", [])) > 0
                or len(result.get("raw_texts", [])) == 0
            )

    @pytest.mark.asyncio
    async def test_run_skip_scout_with_raw_texts(self):
        """测试有预置文本时跳过 Scout"""
        workflow = InsightWorkflow()
        mock_briefing = make_sample_briefing()

        with (
            patch("app.services.agents.workflow.scout_node") as mock_scout,
            patch("app.services.agents.workflow.distiller_node") as mock_distiller,
            patch("app.services.agents.workflow.critic_node") as mock_critic,
            patch("app.services.agents.workflow.memory_editor_node") as mock_editor,
        ):
            mock_distiller.distill_batch = AsyncMock(return_value=[mock_briefing])
            mock_critic.review_batch = AsyncMock(
                return_value=[make_approved_review()]
            )
            mock_editor.process_batch = AsyncMock(return_value=[mock_briefing])

            workflow = InsightWorkflow(
                scout=mock_scout,
                distiller=mock_distiller,
                critic=mock_critic,
                editor=mock_editor,
            )

            await workflow.run(
                topic="AI",
                raw_texts=["预置的原始文本内容，足够长以通过各种检查。"],
            )

            # Scout 不应该被调用
            mock_scout.search_topic.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_distiller_error(self):
        """测试 Distiller 错误处理"""
        workflow = InsightWorkflow()

        with (
            patch("app.services.agents.workflow.distiller_node") as mock_distiller,
            patch("app.services.agents.workflow.critic_node") as mock_critic,
            patch("app.services.agents.workflow.memory_editor_node") as mock_editor,
        ):
            mock_distiller.distill_batch = AsyncMock(
                side_effect=Exception("Distiller failed")
            )

            workflow = InsightWorkflow(
                distiller=mock_distiller,
                critic=mock_critic,
                editor=mock_editor,
            )

            result = await workflow.run(
                topic="AI",
                raw_texts=["测试文本内容。"],
            )

            assert len(result.get("errors", [])) > 0

    @pytest.mark.asyncio
    async def test_run_critic_error(self):
        """测试 Critic 错误处理"""
        workflow = InsightWorkflow()
        mock_briefing = make_sample_briefing()

        with (
            patch("app.services.agents.workflow.distiller_node") as mock_distiller,
            patch("app.services.agents.workflow.critic_node") as mock_critic,
            patch("app.services.agents.workflow.memory_editor_node") as mock_editor,
        ):
            mock_distiller.distill_batch = AsyncMock(return_value=[mock_briefing])
            mock_critic.review_batch = AsyncMock(
                side_effect=Exception("Critic failed")
            )

            workflow = InsightWorkflow(
                distiller=mock_distiller,
                critic=mock_critic,
                editor=mock_editor,
            )

            result = await workflow.run(
                topic="AI",
                raw_texts=["测试文本内容。"],
            )

            assert len(result.get("errors", [])) > 0

    @pytest.mark.asyncio
    async def test_route_after_critic_approved(self):
        """测试 Critic 后路由 - 通过"""
        workflow = InsightWorkflow()

        state = {
            "draft_insights": [{"category": "AI"}],
            "final_briefings": [make_sample_briefing()],
            "retry_count": 0,
        }

        route = workflow._route_after_critic(state)
        assert route == "approved"

    @pytest.mark.asyncio
    async def test_route_after_critic_rejected(self):
        """测试 Critic 后路由 - 拒绝（可重试）"""
        workflow = InsightWorkflow()

        state = {
            "draft_insights": [{"category": "AI"}],
            "final_briefings": [],
            "retry_count": 1,
        }

        route = workflow._route_after_critic(state)
        assert route == "rejected"

    @pytest.mark.asyncio
    async def test_route_after_critic_max_retries(self):
        """测试 Critic 后路由 - 超过最大重试次数"""
        workflow = InsightWorkflow(max_retry=3)

        state = {
            "draft_insights": [{"category": "AI"}],
            "final_briefings": [],
            "retry_count": 3,
        }

        route = workflow._route_after_critic(state)
        assert route == "max_retries_reached"

    @pytest.mark.asyncio
    async def test_contradictory_data_extreme_test(self):
        """极限测试: 注入逻辑矛盾的假数据

        验证 CriticNode 能否成功触发阻断逻辑。
        """
        workflow = InsightWorkflow()

        # 创建充满矛盾的洞见
        contradictory_briefing = FinalBriefing(
            category="矛盾测试",
            core_thesis="所有科技公司都在裁员，同时又在大规模招聘",
            logic_chain=[
                LogicPoint(
                    premise="多家科技公司在 2024 年宣布裁员超过 10000 人",
                    conclusion="科技行业正在经历严重的衰退",
                ),
                LogicPoint(
                    premise="同一时期的数据显示科技岗位招聘数量增长了 50%",
                    conclusion="科技行业正在蓬勃发展",
                ),
            ],
            sources=[
                Source(name="TestSource", url="https://example.com/test"),
            ],
            confidence_score=0.2,
        )

        # 创建拒绝评审（低置信度）
        rejected_review = CriticReview(
            is_approved=False,
            confidence_score=0.2,
            feedback="逻辑自相矛盾：裁员和招聘增长不能同时得出衰退和蓬勃发展的结论",
            missing_evidence=["缺少对裁员和招聘数据的综合分析"],
            logic_issues=[
                "前提1和前提2的结论相互矛盾",
                "未区分不同类型岗位的变化",
            ],
        )

        with (
            patch("app.services.agents.workflow.distiller_node") as mock_distiller,
            patch("app.services.agents.workflow.critic_node") as mock_critic,
            patch("app.services.agents.workflow.memory_editor_node") as mock_editor,
        ):
            mock_distiller.distill_batch = AsyncMock(
                return_value=[contradictory_briefing]
            )
            mock_critic.review_batch = AsyncMock(return_value=[rejected_review])

            workflow = InsightWorkflow(
                distiller=mock_distiller,
                critic=mock_critic,
                editor=mock_editor,
                max_retry=2,
            )

            result = await workflow.run(
                topic="科技行业",
                raw_texts=["充满矛盾的测试数据..."],
            )

            # 验证 Critic 成功阻断了矛盾洞见
            assert len(result.get("final_briefings", [])) == 0
            # 验证重试计次正确递增
            assert result.get("retry_count", 0) >= 2
            # 验证有反馈记录
            feedback = result.get("critic_feedback", [])
            assert len(feedback) > 0
            # 验证 Editor 未被调用
            mock_editor.process_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_count_increments(self):
        """测试重试计数正确递增"""
        workflow = InsightWorkflow()
        mock_briefing = make_sample_briefing()
        rejected_review = make_rejected_review()

        with (
            patch("app.services.agents.workflow.distiller_node") as mock_distiller,
            patch("app.services.agents.workflow.critic_node") as mock_critic,
            patch("app.services.agents.workflow.memory_editor_node") as mock_editor,
        ):
            mock_distiller.distill_batch = AsyncMock(return_value=[mock_briefing])
            mock_critic.review_batch = AsyncMock(return_value=[rejected_review])

            workflow = InsightWorkflow(
                distiller=mock_distiller,
                critic=mock_critic,
                editor=mock_editor,
                max_retry=5,
            )

            result = await workflow.run(
                topic="AI",
                raw_texts=["测试文本..."],
            )

            # 重试次数应该等于 max_retry
            assert result.get("retry_count", 0) == 5

    def test_global_instance(self):
        """测试全局实例"""
        from app.services.agents.workflow import insight_workflow

        assert insight_workflow is not None
        assert isinstance(insight_workflow, InsightWorkflow)
