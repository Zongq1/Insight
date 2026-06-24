"""CriticNode - 红队审稿人

作为系统内最核心的"质量门神"，逐条审视洞见，
检查逻辑跳跃、数据孤证或明显的事实冲突。
"""

import logging
from typing import Optional

from pydantic import BaseModel, Field

from app.core.exceptions import LLMError
from app.models.llm import FinalBriefing
from app.services.llm.client import llm_client
from app.services.prompts.critic_prompts import CRITIC_SYSTEM_PROMPT, CRITIC_USER_PROMPT

logger = logging.getLogger(__name__)


class CriticReview(BaseModel):
    """Critic 评审结果"""

    is_approved: bool = Field(..., description="是否通过评审")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="置信度评分"
    )
    feedback: str = Field(..., description="评审反馈")
    missing_evidence: list[str] = Field(
        default_factory=list, description="缺失的证据"
    )
    suggested_improvements: list[str] = Field(
        default_factory=list, description="改进建议"
    )
    logic_issues: list[str] = Field(
        default_factory=list, description="逻辑问题"
    )


class CriticNode:
    """CriticNode - 红队审稿人

    逐条审视 DraftInsight，检查逻辑跳跃、数据孤证或明显的事实冲突。
    """

    def __init__(self):
        self.system_prompt = CRITIC_SYSTEM_PROMPT
        self.approval_threshold = 0.35  # 通过阈值（RSS 源文章不完全匹配主题，放宽标准）

    async def review(
        self, insight: FinalBriefing, context: str = ""
    ) -> CriticReview:
        """评审洞见

        Args:
            insight: 待评审的洞见
            context: 额外上下文信息（可选）

        Returns:
            CriticReview 评审结果
        """
        try:
            # 构建评审提示
            user_prompt = self._build_review_prompt(insight, context)

            # 调用 LLM 进行评审
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            review = await llm_client.extract(
                response_model=CriticReview,
                messages=messages,
            )

            # 根据阈值判断是否通过
            review.is_approved = review.confidence_score >= self.approval_threshold

            logger.info(
                f"Critic review: approved={review.is_approved}, "
                f"confidence={review.confidence_score}"
            )

            return review

        except LLMError as e:
            logger.error(f"Critic review failed: {e}")
            # 返回低置信度的拒绝评审
            return CriticReview(
                is_approved=False,
                confidence_score=0.0,
                feedback=f"评审过程出错: {str(e)}",
                missing_evidence=["无法完成评审"],
                suggested_improvements=["请重新提交"],
                logic_issues=["评审系统错误"],
            )

    async def review_batch(
        self, insights: list[FinalBriefing], context: str = ""
    ) -> list[CriticReview]:
        """批量评审洞见（并行处理）

        Args:
            insights: 待评审的洞见列表
            context: 额外上下文信息

        Returns:
            CriticReview 列表
        """
        import asyncio

        tasks = [self.review(insight, context) for insight in insights]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        reviews = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Review insight {i+1} failed: {result}")
                reviews.append(CriticReview(
                    is_approved=False,
                    confidence_score=0.0,
                    feedback=f"评审出错: {str(result)}",
                    missing_evidence=[],
                    suggested_improvements=[],
                    logic_issues=[],
                ))
            else:
                reviews.append(result)

        approved_count = sum(1 for r in reviews if r.is_approved)
        logger.info(
            f"Critic batch review: {approved_count}/{len(reviews)} approved"
        )

        return reviews

    def _build_review_prompt(
        self, insight: FinalBriefing, context: str
    ) -> str:
        """构建评审提示"""
        logic_chain_text = "\n".join(
            f"  {i}. premise: {p.premise} → conclusion: {p.conclusion}"
            for i, p in enumerate(insight.logic_chain, 1)
        )
        sources_text = "\n".join(
            f"  - {s.name}: {s.url}" for s in insight.sources
        )

        prompt = CRITIC_USER_PROMPT.format(
            category=insight.category,
            core_thesis=insight.core_thesis,
            logic_chain=logic_chain_text or "  (none)",
            sources=sources_text or "  (none)",
            confidence_score=insight.confidence_score,
            historical_insight=insight.historical_insight or "(none)",
        )

        if context:
            prompt += f"\n【额外上下文】\n{context}\n"

        return prompt


# 全局 CriticNode 实例
critic_node = CriticNode()
