"""节点级重试策略

使用 tenacity 实现结构化重试，支持指数退避。
"""

import logging
from functools import wraps
from typing import Callable

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import LLMError, NewsAPIError, VectorDatabaseError

logger = logging.getLogger(__name__)


def llm_retry(max_attempts: int = 3):
    """LLM 调用重试装饰器

    处理速率限制和临时故障。
    指数退避: 2-30 秒。
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((LLMError, TimeoutError)),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"LLM call retry {retry_state.attempt_number}/{max_attempts}: "
            f"{retry_state.outcome.exception() if retry_state.outcome else 'unknown'}"
        ),
    )


def api_retry(max_attempts: int = 2):
    """外部 API 调用重试装饰器

    处理 HTTP 错误和网络故障。
    指数退避: 1-10 秒。
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((NewsAPIError, TimeoutError)),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"API call retry {retry_state.attempt_number}/{max_attempts}: "
            f"{retry_state.outcome.exception() if retry_state.outcome else 'unknown'}"
        ),
    )


def vector_retry(max_attempts: int = 2):
    """向量数据库重试装饰器

    处理数据库连接和查询故障。
    固定间隔: 1 秒。
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((VectorDatabaseError, TimeoutError)),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"Vector DB retry {retry_state.attempt_number}/{max_attempts}: "
            f"{retry_state.outcome.exception() if retry_state.outcome else 'unknown'}"
        ),
    )
