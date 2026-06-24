"""LLM 客户端测试

测试 Instructor 客户端封装的功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import LLMError, LLMRetryExhaustedError
from app.models.llm import FinalBriefing, LogicPoint, Source
from app.services.llm.client import LLMClient


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI 客户端"""
    with patch("app.services.llm.client.AsyncOpenAI") as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_instructor():
    """Mock Instructor"""
    with patch("app.services.llm.client.instructor") as mock:
        mock_client = MagicMock()
        mock.from_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def llm_client(mock_openai_client, mock_instructor):
    """创建 LLM 客户端实例"""
    return LLMClient(
        api_key="test-key",
        model="gpt-4o",
        max_retries=3,
    )


class TestLLMClient:
    """LLM 客户端测试"""

    def test_init_with_custom_params(self, mock_openai_client, mock_instructor):
        """测试使用自定义参数初始化"""
        client = LLMClient(
            api_key="custom-key",
            model="gpt-3.5-turbo",
            max_retries=5,
        )
        assert client.api_key == "custom-key"
        assert client.model == "gpt-3.5-turbo"
        assert client.max_retries == 5

    def test_init_with_base_url(self, mock_openai_client, mock_instructor):
        """测试使用自定义 base_url 初始化"""
        client = LLMClient(
            api_key="test-key",
            base_url="https://custom-api.example.com/v1",
            model="gpt-4o",
        )
        assert client.base_url == "https://custom-api.example.com/v1"

    @pytest.mark.asyncio
    async def test_extract_success(self, llm_client, mock_instructor):
        """测试成功的结构化提取"""
        # Mock Instructor 响应
        mock_briefing = FinalBriefing(
            category="AI",
            core_thesis="这是一个测试的核心论点用于验证",
            logic_chain=[
                LogicPoint(
                    premise="这是一个测试的前提用于验证提取",
                    conclusion="这是一个测试的结论用于验证提取",
                ),
                LogicPoint(
                    premise="这是另一个测试前提用于验证提取",
                    conclusion="这是另一个测试结论用于验证提取",
                ),
            ],
            sources=[
                Source(name="Test", url="https://example.com"),
            ],
            confidence_score=0.8,
        )

        mock_instructor.chat.completions.create = AsyncMock(
            return_value=mock_briefing
        )

        result = await llm_client.extract(
            response_model=FinalBriefing,
            messages=[{"role": "user", "content": "test"}],
        )

        assert isinstance(result, FinalBriefing)
        assert result.category == "AI"
        assert result.confidence_score == 0.8

    @pytest.mark.asyncio
    async def test_extract_generic_error(self, llm_client, mock_instructor):
        """测试通用错误"""
        mock_instructor.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("API Error")
        )

        with pytest.raises(LLMError) as exc_info:
            await llm_client.extract(
                response_model=FinalBriefing,
                messages=[{"role": "user", "content": "test"}],
            )

        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_insight(self, llm_client, mock_instructor):
        """测试 extract_insight 便捷方法"""
        mock_briefing = FinalBriefing(
            category="AI",
            core_thesis="这是一个测试的核心论点用于验证",
            logic_chain=[
                LogicPoint(
                    premise="这是一个测试的前提用于验证提取",
                    conclusion="这是一个测试的结论用于验证提取",
                ),
                LogicPoint(
                    premise="这是另一个测试前提用于验证提取",
                    conclusion="这是另一个测试结论用于验证提取",
                ),
            ],
            sources=[
                Source(name="Test", url="https://example.com"),
            ],
            confidence_score=0.8,
        )

        mock_instructor.chat.completions.create = AsyncMock(
            return_value=mock_briefing
        )

        result = await llm_client.extract_insight("这是一篇测试文章")

        assert isinstance(result, FinalBriefing)
        # 验证调用参数
        call_args = mock_instructor.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages")
        assert messages is not None
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "这是一篇测试文章" in messages[1]["content"]
