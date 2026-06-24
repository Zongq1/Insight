"""ScoutNode 测试"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NewsAPIError
from app.services.agents.scout import (
    Article,
    NewsAPIClient,
    ScoutNode,
    ScoutResult,
)


@pytest.fixture
def mock_news_client():
    """Mock News API 客户端"""
    with patch("app.services.agents.scout.NewsAPIClient") as mock:
        yield mock


@pytest.fixture
def scout_node(mock_news_client):
    """创建 ScoutNode 实例"""
    return ScoutNode()


class TestArticle:
    """Article 模型测试"""

    def test_valid_article(self):
        """测试有效的 Article 创建"""
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            source="Test Source",
            published_at=datetime.now(),
            description="Test description",
            content="Test content",
        )

        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.source == "Test Source"

    def test_article_with_minimal_fields(self):
        """测试最小字段的 Article"""
        article = Article(
            title="Test",
            url="https://example.com",
            source="Test",
        )

        assert article.title == "Test"
        assert article.published_at is None
        assert article.description is None
        assert article.content is None


class TestNewsAPIClient:
    """News API 客户端测试"""

    def test_init_with_api_key(self):
        """测试使用 API Key 初始化"""
        client = NewsAPIClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_init_without_api_key(self):
        """测试没有 API Key 的初始化"""
        # 这里应该记录警告
        client = NewsAPIClient(api_key=None)
        # 在测试环境中，NEWS_API_KEY 可能未配置

    @pytest.mark.asyncio
    async def test_search_everything_success(self):
        """测试成功的搜索"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/article",
                    "source": {"name": "Test Source"},
                    "publishedAt": "2024-01-15T12:00:00Z",
                    "description": "Test description",
                    "content": "Test content",
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            client = NewsAPIClient(api_key="test-key")
            articles = await client.search_everything("AI")

            assert len(articles) == 1
            assert articles[0].title == "Test Article"
            assert articles[0].source == "Test Source"

    @pytest.mark.asyncio
    async def test_search_everything_error(self):
        """测试搜索错误"""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Network error")

            client = NewsAPIClient(api_key="test-key")

            with pytest.raises(NewsAPIError):
                await client.search_everything("AI")


class TestScoutNode:
    """ScoutNode 测试"""

    def test_generate_search_keywords(self, scout_node):
        """测试生成搜索关键词"""
        keywords = scout_node.generate_search_keywords("AI")

        assert "AI" in keywords
        assert len(keywords) >= 1

    @pytest.mark.asyncio
    async def test_search_topic_success(self, scout_node):
        """测试成功搜索主题"""
        # Mock News API 响应
        mock_articles = [
            Article(
                title="AI Article 1",
                url="https://example.com/1",
                source="Source 1",
                content="Content 1 " * 50,  # 足够长的内容
            ),
            Article(
                title="AI Article 2",
                url="https://example.com/2",
                source="Source 2",
                content="Content 2 " * 50,
            ),
        ]

        scout_node.news_client.search_everything = AsyncMock(
            return_value=mock_articles
        )

        result = await scout_node.search_topic("AI", ["artificial intelligence"])

        assert isinstance(result, ScoutResult)
        assert result.topic == "AI"
        assert len(result.articles) == 2
        assert len(result.raw_texts) == 2

    @pytest.mark.asyncio
    async def test_search_topic_with_duplicates(self, scout_node):
        """测试搜索主题（包含重复文章）"""
        # Mock 返回重复文章
        mock_articles = [
            Article(
                title="Same Article",
                url="https://example.com/same",
                source="Source",
                content="Content " * 50,
            ),
            Article(
                title="Same Article",
                url="https://example.com/same",
                source="Source",
                content="Content " * 50,
            ),
        ]

        scout_node.news_client.search_everything = AsyncMock(
            return_value=mock_articles
        )

        result = await scout_node.search_topic("AI", ["AI"])

        # 应该去重
        assert len(result.articles) == 1

    @pytest.mark.asyncio
    async def test_search_topic_api_error(self, scout_node):
        """测试 API 错误处理"""
        scout_node.news_client.search_everything = AsyncMock(
            side_effect=NewsAPIError("API Error")
        )

        result = await scout_node.search_topic("AI", ["AI"])

        # 错误应该被优雅处理
        assert isinstance(result, ScoutResult)
        assert len(result.articles) == 0
