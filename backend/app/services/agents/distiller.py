"""DistillerNode - 提纯者

深度清洗原始文本，剥离营销修辞和情绪化词汇，
提取事实、数据和逻辑链条。
"""

import logging
from typing import Optional

from app.core.exceptions import LLMError
from app.models.llm import FinalBriefing
from app.services.llm.client import llm_client
from app.services.llm.context_manager import build_context, estimate_tokens
from app.services.llm.cost_tracker import cost_tracker
from app.services.prompts.distiller_prompts import (
    DISTILLER_SYSTEM_PROMPT,
    DISTILLER_TOPIC_SECTION,
    DISTILLER_USER_PROMPT,
)

logger = logging.getLogger(__name__)

# Reflexion 反馈注入后缀
REFLEXION_SUFFIX = """

## Previous Attempt Feedback
Your previous draft was rejected for the following reasons:
{feedback}

Please address these issues in your new draft. Focus on:
- Strengthening weak evidence with concrete data points
- Adding missing logical links in the reasoning chain
- Improving confidence calibration (don't overstate weak evidence)
- Ensuring the core thesis is specific and falsifiable"""


class DistillerNode:
    """DistillerNode - 提纯者

    阅读原始文本，剥离营销修辞和情绪化词汇，
    提取事实、数据和逻辑链条。
    """

    def __init__(self):
        self.system_prompt = DISTILLER_SYSTEM_PROMPT

    async def distill(
        self,
        text: str,
        topic: str = "",
        prior_feedback: Optional[str] = None,
    ) -> Optional[FinalBriefing]:
        """提纯文本，提取洞见

        Args:
            text: 原始文本内容
            topic: 目标主题（可选）
            prior_feedback: Critic 的先前反馈（用于 Reflexion 重试）

        Returns:
            FinalBriefing 或 None（如果提取失败）
        """
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for distillation")
            return None

        try:
            # 构建系统提示（如有先前反馈则注入 Reflexion 指令）
            system_prompt = self.system_prompt
            if prior_feedback:
                system_prompt += REFLEXION_SUFFIX.format(feedback=prior_feedback)

            # 构建用户提示（使用 context_manager 管理 token 预算）
            user_prompt = self._build_user_prompt(text, topic)

            # 记录 token 估算
            est_tokens = estimate_tokens(system_prompt + user_prompt)
            logger.info(f"Distiller input: ~{est_tokens} tokens")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            result = await llm_client.extract(
                response_model=FinalBriefing,
                messages=messages,
            )

            logger.info(
                f"Distilled insight: category={result.category}, "
                f"confidence={result.confidence_score}"
            )

            return result

        except LLMError as e:
            logger.error(f"Distillation failed: {e}")
            return None

    async def distill_batch(
        self,
        texts: list[str],
        topic: str = "",
        prior_feedback: Optional[str] = None,
        max_texts: int = 5,
    ) -> list[FinalBriefing]:
        """批量提纯文本（并行处理，限制数量）

        Args:
            texts: 原始文本列表
            topic: 目标主题
            prior_feedback: Critic 的先前反馈（用于 Reflexion 重试）
            max_texts: 最多处理的文本数量（默认 5）

        Returns:
            FinalBriefing 列表
        """
        import asyncio

        # 限制处理数量（MiMo API 每次调用 ~20s，1 篇可控制在 45s 内）
        texts_to_process = texts[:1]
        if len(texts) > max_texts:
            logger.info(f"Limiting distillation: {len(texts)} -> {max_texts} texts")

        # 并行处理
        tasks = [
            self.distill(text, topic, prior_feedback=prior_feedback)
            for text in texts_to_process
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        briefings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Distill text {i+1} failed: {result}")
            elif result is not None:
                briefings.append(result)

        logger.info(f"Distilled {len(briefings)}/{len(texts_to_process)} texts successfully")
        return briefings

    def _build_user_prompt(self, text: str, topic: str) -> str:
        """构建用户提示"""
        topic_section = ""
        if topic:
            topic_section = DISTILLER_TOPIC_SECTION.format(topic=topic)

        prompt = DISTILLER_USER_PROMPT.format(
            topic_section=topic_section,
            text=text,
        )

        # 限制文本长度，加速 LLM 处理（MiMo API 对长 prompt 较慢）
        if len(prompt) > 1500:
            prompt = prompt[:1500] + "\n\n[文本已截断]"

        return prompt


# 全局 DistillerNode 实例
distiller_node = DistillerNode()
