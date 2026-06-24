"""LangGraph 状态定义测试"""

import pytest
from datetime import date

from app.core.state import GraphState, DraftInsight, CriticFeedback
from app.models.llm import FinalBriefing, LogicPoint, Source


class TestGraphState:
    """GraphState 类型测试"""

    def test_graph_state_creation(self):
        """测试 GraphState 创建"""
        state: GraphState = {
            "target_topic": "AI",
            "raw_texts": ["text1", "text2"],
            "draft_insights": [{"insight": "test"}],
            "critic_feedback": ["feedback1"],
            "final_briefings": [],
            "retry_count": 0,
            "current_index": 0,
            "errors": [],
        }

        assert state["target_topic"] == "AI"
        assert len(state["raw_texts"]) == 2
        assert state["retry_count"] == 0

    def test_graph_state_defaults(self):
        """测试 GraphState 默认值"""
        state: GraphState = {
            "target_topic": "Blockchain",
            "raw_texts": [],
            "draft_insights": [],
            "critic_feedback": [],
            "final_briefings": [],
            "retry_count": 0,
            "current_index": 0,
            "errors": [],
        }

        assert state["target_topic"] == "Blockchain"
        assert state["raw_texts"] == []
        assert state["draft_insights"] == []
        assert state["retry_count"] == 0

    def test_graph_state_with_briefings(self):
        """测试包含 final_briefings 的 GraphState"""
        briefing = FinalBriefing(
            category="AI",
            core_thesis="AI技术正在快速发展并改变世界格局",
            logic_chain=[
                LogicPoint(premise="全球AI投资2024年增长了200个百分点", conclusion="AI产业正处于爆发式增长的初期阶段"),
                LogicPoint(premise="主要科技公司纷纷加大AI研发投入", conclusion="AI技术已成为企业核心竞争力的关键因素"),
            ],
            sources=[Source(name="Test", url="https://example.com")],
            confidence_score=0.85,
        )

        state: GraphState = {
            "target_topic": "AI",
            "raw_texts": ["raw text"],
            "draft_insights": [],
            "critic_feedback": [],
            "final_briefings": [briefing],
            "retry_count": 0,
            "current_index": 0,
            "errors": [],
        }

        assert len(state["final_briefings"]) == 1
        assert state["final_briefings"][0].category == "AI"

    def test_graph_state_retry_count(self):
        """测试重试计数"""
        state: GraphState = {
            "target_topic": "AI",
            "raw_texts": [],
            "draft_insights": [],
            "critic_feedback": ["needs more evidence"],
            "final_briefings": [],
            "retry_count": 3,
            "current_index": 0,
            "errors": ["error1", "error2"],
        }

        assert state["retry_count"] == 3
        assert len(state["errors"]) == 2


class TestDraftInsight:
    """DraftInsight 类型测试"""

    def test_draft_insight_creation(self):
        """测试 DraftInsight 创建"""
        draft: DraftInsight = {
            "category": "AI",
            "core_thesis": "AI is transforming industries",
            "logic_chain": [
                {"premise": "premise1", "conclusion": "conclusion1"},
            ],
            "sources": [{"name": "Test", "url": "https://example.com"}],
            "confidence_score": 0.7,
            "needs_more_evidence": False,
        }

        assert draft["category"] == "AI"
        assert draft["confidence_score"] == 0.7
        assert draft["needs_more_evidence"] is False

    def test_draft_insight_needs_evidence(self):
        """测试需要更多证据的 DraftInsight"""
        draft: DraftInsight = {
            "category": "Quantum",
            "core_thesis": "Quantum computing will break encryption",
            "logic_chain": [],
            "sources": [],
            "confidence_score": 0.3,
            "needs_more_evidence": True,
        }

        assert draft["needs_more_evidence"] is True
        assert draft["confidence_score"] < 0.5


class TestCriticFeedback:
    """CriticFeedback 类型测试"""

    def test_critic_feedback_approved(self):
        """测试通过的 CriticFeedback"""
        feedback: CriticFeedback = {
            "insight_index": 0,
            "is_approved": True,
            "feedback": "Well structured argument",
            "missing_evidence": [],
            "suggested_improvements": [],
        }

        assert feedback["is_approved"] is True
        assert feedback["insight_index"] == 0
        assert len(feedback["missing_evidence"]) == 0

    def test_critic_feedback_rejected(self):
        """测试被拒绝的 CriticFeedback"""
        feedback: CriticFeedback = {
            "insight_index": 2,
            "is_approved": False,
            "feedback": "Logic chain has gaps",
            "missing_evidence": ["source for claim X", "data for statistic Y"],
            "suggested_improvements": ["Add more sources", "Verify data accuracy"],
        }

        assert feedback["is_approved"] is False
        assert len(feedback["missing_evidence"]) == 2
        assert len(feedback["suggested_improvements"]) == 2

    def test_critic_feedback_index(self):
        """测试 insight_index 边界"""
        feedback: CriticFeedback = {
            "insight_index": 4,
            "is_approved": True,
            "feedback": "Good",
            "missing_evidence": [],
            "suggested_improvements": [],
        }

        assert feedback["insight_index"] == 4
