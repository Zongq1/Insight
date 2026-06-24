"""自定义异常定义"""

from typing import Any, Optional


class InsightBaseException(Exception):
    """基础异常类"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class LLMError(InsightBaseException):
    """LLM 调用异常"""

    pass


class LLMRetryExhaustedError(LLMError):
    """LLM 重试次数耗尽异常"""

    def __init__(self, message: str, attempts: int, last_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            details={"attempts": attempts, "last_error": str(last_error)},
        )


class ValidationError(InsightBaseException):
    """数据验证异常"""

    pass


class DatabaseError(InsightBaseException):
    """数据库操作异常"""

    pass


class VectorDatabaseError(InsightBaseException):
    """向量数据库异常"""

    pass


class CostLimitExceededError(InsightBaseException):
    """成本超出限制异常"""

    def __init__(self, message: str, current_cost: float, limit: float):
        super().__init__(
            message=message,
            details={"current_cost": current_cost, "limit": limit},
        )


class NewsAPIError(InsightBaseException):
    """News API 调用异常"""

    pass


class ContentExtractionError(InsightBaseException):
    """内容提取异常"""

    pass
