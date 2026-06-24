"""LangGraph 状态定义

定义多智能体工作流的共享状态。
"""

import operator
from typing import Annotated, TypedDict

from app.models.llm import FinalBriefing


class GraphState(TypedDict):
    """LangGraph 状态

    这是多智能体之间共享的状态白板。
    使用 Annotated 和 operator.add 来支持状态累加。
    """

    # 目标主题
    target_topic: str

    # 原始文本（支持累加）
    raw_texts: Annotated[list[str], operator.add]

    # 草稿洞见
    draft_insights: list[dict]

    # Critic 反馈
    critic_feedback: Annotated[list[str], operator.add]

    # 最终洞见
    final_briefings: list[FinalBriefing]

    # 重试计数
    retry_count: int

    # 当前处理的文本索引
    current_index: int

    # Critic 反馈文本（供 Distiller 重试时参考）
    critic_feedback_text: str

    # 错误信息
    errors: Annotated[list[str], operator.add]


class DraftInsight(TypedDict):
    """草稿洞见结构"""

    category: str
    core_thesis: str
    logic_chain: list[dict]
    sources: list[dict]
    confidence_score: float
    needs_more_evidence: bool


class CriticFeedback(TypedDict):
    """Critic 反馈结构"""

    insight_index: int
    is_approved: bool
    feedback: str
    missing_evidence: list[str]
    suggested_improvements: list[str]
