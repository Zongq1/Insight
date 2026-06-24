"""重试策略测试"""

import pytest

from app.core.exceptions import LLMError, NewsAPIError, VectorDatabaseError
from app.core.retry import api_retry, llm_retry, vector_retry


class TestLLMRetry:
    """LLM 重试测试"""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """成功调用不重试"""
        call_count = 0

        @llm_retry(max_attempts=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await success_func()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_llm_error(self):
        """LLM 错误触发重试"""
        call_count = 0

        @llm_retry(max_attempts=3)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise LLMError("Temporary error")
            return "ok"

        result = await flaky_func()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """重试耗尽抛出异常"""
        call_count = 0

        @llm_retry(max_attempts=2)
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise LLMError("Persistent error")

        with pytest.raises(LLMError):
            await always_fail()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_other_error(self):
        """非 LLM 错误不重试"""
        call_count = 0

        @llm_retry(max_attempts=3)
        async def other_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not an LLM error")

        with pytest.raises(ValueError):
            await other_error()

        assert call_count == 1


class TestAPIRetry:
    """API 重试测试"""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """成功调用不重试"""
        call_count = 0

        @api_retry(max_attempts=2)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await success_func()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_news_api_error(self):
        """News API 错误触发重试"""
        call_count = 0

        @api_retry(max_attempts=2)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NewsAPIError("API error")
            return "ok"

        result = await flaky_func()
        assert result == "ok"
        assert call_count == 2


class TestVectorRetry:
    """向量数据库重试测试"""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """成功调用不重试"""
        call_count = 0

        @vector_retry(max_attempts=2)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await success_func()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_vector_error(self):
        """向量数据库错误触发重试"""
        call_count = 0

        @vector_retry(max_attempts=2)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise VectorDatabaseError("DB error")
            return "ok"

        result = await flaky_func()
        assert result == "ok"
        assert call_count == 2
