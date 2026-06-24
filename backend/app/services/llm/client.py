"""Instructor 客户端封装

提供 LLM 结构化输出的统一接口。
使用 Instructor 库确保 LLM 输出符合 Pydantic 模型定义。
"""

import logging
from typing import Type, TypeVar

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings
from app.core.exceptions import LLMError, LLMRetryExhaustedError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """LLM 客户端

    封装 Instructor 和 OpenAI 客户端，提供结构化输出功能。
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int | None = None,
    ):
        """初始化 LLM 客户端

        Args:
            api_key: OpenAI API Key，默认从配置读取
            base_url: API 基础 URL，默认从配置读取
            model: LLM 模型名称，默认从配置读取
            max_retries: 最大重试次数，默认从配置读取
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model = model or settings.LLM_MODEL
        self.max_retries = max_retries or settings.LLM_MAX_RETRIES

        # 初始化 OpenAI 异步客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        # 使用 Instructor 包装客户端
        # mode=instructor.Mode.TOOLS 是最稳定的模式
        self.instructor_client = instructor.from_openai(
            self.client,
            mode=instructor.Mode.TOOLS,
        )

    async def extract(
        self,
        response_model: Type[T],
        messages: list[dict[str, str]],
        max_retries: int | None = None,
    ) -> T:
        """提取结构化输出

        使用 Instructor 将 LLM 输出转换为指定的 Pydantic 模型。

        Args:
            response_model: 目标 Pydantic 模型类型
            messages: 对话消息列表
            max_retries: 最大重试次数，默认使用实例配置

        Returns:
            符合 response_model 的结构化数据

        Raises:
            LLMRetryExhaustedError: 重试次数耗尽
            LLMError: 其他 LLM 调用错误
        """
        retries = max_retries if max_retries is not None else self.max_retries

        try:
            logger.info(
                f"Calling LLM with model={self.model}, "
                f"response_model={response_model.__name__}, "
                f"max_retries={retries}"
            )

            result = await self.instructor_client.chat.completions.create(
                model=self.model,
                response_model=response_model,
                max_retries=retries,
                messages=messages,
            )

            logger.info(f"LLM extraction successful: {response_model.__name__}")
            return result

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"LLM call failed ({error_type}): {e}")

            # Check if it's a retry exhausted error
            if "RetryExhausted" in error_type or "retry" in str(e).lower():
                raise LLMRetryExhaustedError(
                    message=f"Failed to extract {response_model.__name__} after {retries} retries",
                    attempts=retries,
                    last_error=e,
                )

            raise LLMError(
                message=f"Failed to call LLM: {str(e)}",
                details={"model": self.model, "error": str(e)},
            )

    async def extract_insight(self, text: str) -> "FinalBriefing":
        """从文本中提取洞见

        便捷方法，直接从原始文本提取 FinalBriefing。

        Args:
            text: 原始文本内容

        Returns:
            FinalBriefing 结构化洞见
        """
        from app.models.llm import FinalBriefing

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个冷酷客观的分析师，只提取事实、数据和逻辑链条。"
                    "请从给定的文本中提取核心洞见，包括："
                    "1. 高维分类标签（最多三个单词）"
                    "2. 一句话核心论点（40字以内，禁止形容词堆砌）"
                    "3. 严密的逻辑推演链（2-5个节点）"
                    "4. 信息来源"
                    "5. 如果与历史事件有关联，请指出"
                ),
            },
            {
                "role": "user",
                "content": f"请从以下文本中提取洞见：\n\n{text}",
            },
        ]

        return await self.extract(
            response_model=FinalBriefing,
            messages=messages,
        )


# 全局 LLM 客户端实例
llm_client = LLMClient()
