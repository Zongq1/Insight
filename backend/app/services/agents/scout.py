"""ScoutNode - 星海寻路人

负责广度检索，根据主题搜索相关文章。
支持 LLM 驱动的搜索策略生成（Tool Use 模式）。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import NewsAPIError
from app.services.llm.client import llm_client

logger = logging.getLogger(__name__)


class Article(BaseModel):
    """文章模型"""

    title: str = Field(..., description="文章标题")
    url: str = Field(..., description="文章链接")
    source: str = Field(..., description="来源名称")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    description: Optional[str] = Field(None, description="文章摘要")
    content: Optional[str] = Field(None, description="文章正文")


class ScoutResult(BaseModel):
    """Scout 结果"""

    topic: str = Field(..., description="主题名称")
    articles: list[Article] = Field(default_factory=list, description="检索到的文章")
    raw_texts: list[str] = Field(default_factory=list, description="提取的纯文本")


class NewsAPIClient:
    """News API 客户端

    使用 News API 搜索新闻文章。
    API 文档: https://newsapi.org/docs
    """

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.NEWS_API_KEY
        if not self.api_key:
            logger.warning("NEWS_API_KEY not configured")

    async def search_everything(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        language: str = "en",
        sort_by: str = "relevancy",
        page_size: int = 20,
        page: int = 1,
    ) -> list[Article]:
        """搜索所有文章

        Args:
            query: 搜索关键词
            from_date: 开始日期
            to_date: 结束日期
            language: 语言
            sort_by: 排序方式 (relevancy, popularity, publishedAt)
            page_size: 每页数量
            page: 页码

        Returns:
            文章列表
        """
        if not self.api_key:
            raise NewsAPIError("NEWS_API_KEY not configured")

        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page,
            "apiKey": self.api_key,
        }

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%S")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%S")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/everything",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "ok":
                    raise NewsAPIError(f"News API error: {data.get('message')}")

                articles = []
                for item in data.get("articles", []):
                    article = Article(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        source=item.get("source", {}).get("name", "Unknown"),
                        published_at=self._parse_datetime(item.get("publishedAt")),
                        description=item.get("description"),
                        content=item.get("content"),
                    )
                    articles.append(article)

                logger.info(f"Found {len(articles)} articles for query: {query}")
                return articles

            except httpx.HTTPStatusError as e:
                logger.error(f"News API HTTP error: {e}")
                raise NewsAPIError(f"News API HTTP error: {e}")
            except Exception as e:
                logger.error(f"News API call failed: {e}")
                raise NewsAPIError(f"News API call failed: {e}")

    async def search_top_headlines(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        country: str = "us",
        page_size: int = 20,
        page: int = 1,
    ) -> list[Article]:
        """搜索热门新闻

        Args:
            query: 搜索关键词
            category: 分类 (business, entertainment, general, health, science, sports, technology)
            country: 国家代码
            page_size: 每页数量
            page: 页码

        Returns:
            文章列表
        """
        if not self.api_key:
            raise NewsAPIError("NEWS_API_KEY not configured")

        params = {
            "country": country,
            "pageSize": page_size,
            "page": page,
            "apiKey": self.api_key,
        }

        if query:
            params["q"] = query
        if category:
            params["category"] = category

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/top-headlines",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "ok":
                    raise NewsAPIError(f"News API error: {data.get('message')}")

                articles = []
                for item in data.get("articles", []):
                    article = Article(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        source=item.get("source", {}).get("name", "Unknown"),
                        published_at=self._parse_datetime(item.get("publishedAt")),
                        description=item.get("description"),
                        content=item.get("content"),
                    )
                    articles.append(article)

                logger.info(f"Found {len(articles)} top headlines")
                return articles

            except httpx.HTTPStatusError as e:
                logger.error(f"News API HTTP error: {e}")
                raise NewsAPIError(f"News API HTTP error: {e}")
            except Exception as e:
                logger.error(f"News API call failed: {e}")
                raise NewsAPIError(f"News API call failed: {e}")

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """解析日期时间字符串"""
        if not dt_str:
            return None
        try:
            # News API 使用 ISO 8601 格式
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            return None


class SearchStrategy(BaseModel):
    """LLM 生成的搜索策略"""

    keywords: list[str] = Field(description="搜索关键词列表，3-6 个", min_length=3, max_length=6)
    focus_areas: list[str] = Field(description="重点关注领域，2-4 个", min_length=2, max_length=4)
    reasoning: str = Field(description="选择这些关键词的推理过程")


STRATEGY_PROMPT = """你是一个资深新闻分析师。根据用户给出的主题，生成最优的搜索策略。

要求：
1. 关键词要覆盖主题的不同维度（技术、市场、政策、影响等）
2. 关键词要具体、可搜索，避免太宽泛
3. 每个关键词应该能独立搜到有价值的新闻
4. focus_areas 列出你认为需要重点关注的子领域

当前日期：{current_date}
请搜索最近 7 天的新闻。"""


class ScoutNode:
    """ScoutNode - 星海寻路人

    使用 LLM 生成搜索策略，然后执行多轮搜索。
    支持结果不足时自动调整关键词重试。
    """

    def __init__(self):
        self.news_client = NewsAPIClient()
        self._llm_strategy_enabled = True

    async def generate_strategy(self, topic: str) -> SearchStrategy:
        """使用 LLM 生成搜索策略

        Args:
            topic: 目标主题

        Returns:
            SearchStrategy 包含关键词和推理
        """
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            messages = [
                {
                    "role": "system",
                    "content": STRATEGY_PROMPT.format(current_date=current_date),
                },
                {
                    "role": "user",
                    "content": f"请为以下主题生成搜索策略：{topic}",
                },
            ]

            strategy = await llm_client.extract(
                response_model=SearchStrategy,
                messages=messages,
            )

            logger.info(
                f"LLM strategy for '{topic}': keywords={strategy.keywords}, "
                f"focus={strategy.focus_areas}"
            )
            return strategy

        except Exception as e:
            logger.warning(f"LLM strategy failed, using fallback: {e}")
            return self._fallback_strategy(topic)

    def _fallback_strategy(self, topic: str) -> SearchStrategy:
        """回退策略：基于规则生成关键词"""
        current_year = datetime.now().year
        return SearchStrategy(
            keywords=[
                topic,
                f"{topic} {current_year}",
                f"{topic} analysis",
                f"{topic} trends",
            ],
            focus_areas=["general"],
            reasoning="LLM 不可用，使用回退策略",
        )

    async def search_topic(self, topic: str, keywords: list[str] | None = None) -> ScoutResult:
        """搜索主题相关文章

        分级数据源策略：
        1. NewsNow API（多平台热点，免费，国内直连，优先）
        2. RSS 订阅源（36氪，备选）
        3. LLM 生成摘要（仅测试用，标注为测试数据）

        Args:
            topic: 主题名称
            keywords: 关键词列表（可选，用于过滤）

        Returns:
            ScoutResult 包含文章和提取的文本
        """
        logger.info(f"Searching topic: {topic}, keywords: {keywords}")

        # 阶段 1：NewsNow API（多平台热点）
        newsnow_articles = await self._fetch_newsnow(keywords)

        # 阶段 2：RSS 补充
        all_articles = list(newsnow_articles)
        if len(all_articles) < 5:
            logger.info(f"NewsNow got {len(all_articles)} articles, trying RSS")
            rss_articles = await self._fetch_rss(keywords)
            all_articles.extend(rss_articles)

        # 去重
        unique_articles = self._deduplicate(all_articles)

        # 阶段 3：如果所有在线源都失败，使用 LLM 生成测试数据
        if not unique_articles:
            logger.warning("Scout: all sources returned 0 articles, using LLM test data")
            return await self._generate_fallback_articles(topic)

        logger.info(f"Found {len(unique_articles)} unique articles for topic: {topic}")

        # 提取文章内容
        raw_texts = []
        for article in unique_articles:
            text = self._extract_article_text(article)
            if text:
                raw_texts.append(text)

        return ScoutResult(
            topic=topic,
            articles=unique_articles,
            raw_texts=raw_texts,
        )

    async def _fetch_newsnow(self, keywords: list[str] | None = None) -> list[Article]:
        """从 NewsNow API 抓取多平台热点"""
        try:
            from app.services.agents.newsnow_client import newsnow_client
            return await newsnow_client.fetch_multiple(keywords=keywords)
        except Exception as e:
            logger.warning(f"NewsNow fetch failed: {e}")
            return []

    async def _fetch_rss(self, keywords: list[str] | None = None) -> list[Article]:
        """从 RSS 源抓取文章"""
        try:
            from app.services.agents.rss_client import rss_client
            return await rss_client.fetch_all(keywords=keywords)
        except Exception as e:
            logger.warning(f"RSS fetch failed: {e}")
            return []

    async def _generate_fallback_articles(self, topic: str) -> ScoutResult:
        """在线源全部失败时，用 LLM 生成测试文章

        注意：生成的内容为 LLM 编造的测试数据，仅用于验证流水线。
        正式使用时应确保数据源为真实新闻。
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一位资深新闻分析师。请根据给定主题，生成 3 篇不同角度的深度分析摘要。"
                        "每篇 200-400 字，包含具体数据、事件和趋势分析。"
                        "覆盖技术、市场、政策三个维度。"
                        "注意：这是用于系统测试的模拟数据，请基于真实行业趋势合理推演。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"请为主题「{topic}」生成 3 篇深度分析摘要，每篇包含具体数据和趋势判断。",
                },
            ]

            from pydantic import BaseModel

            class FallbackArticle(BaseModel):
                title: str
                content: str

            class FallbackArticles(BaseModel):
                articles: list[FallbackArticle]

            result = await llm_client.extract(
                response_model=FallbackArticles,
                messages=messages,
            )

            articles = []
            raw_texts = []
            for i, a in enumerate(result.articles):
                article = Article(
                    title=f"[测试] {a.title}",
                    url=f"https://test-data.example/{i}",
                    source="[测试数据 - LLM生成]",
                    description=a.content[:200],
                    content=a.content,
                )
                articles.append(article)
                raw_texts.append(a.content)

            logger.info(f"Scout fallback: generated {len(articles)} test articles via LLM")
            return ScoutResult(topic=topic, articles=articles, raw_texts=raw_texts)

        except Exception as e:
            logger.error(f"Scout fallback failed: {e}")
            return self._hardcoded_fallback(topic)

    def _hardcoded_fallback(self, topic: str) -> ScoutResult:
        """硬编码测试数据，确保流水线始终有输入

        注意：这是测试用的模拟数据，不是真实新闻。
        """
        texts = [
            f"【{topic}行业动态】近期{topic}领域出现多项重要进展。"
            f"据行业报告显示，全球{topic}市场规模预计在2026年达到新的高峰，"
            f"同比增长超过25%。多家头部企业加大投入，推动技术创新和商业化落地。"
            f"分析人士指出，这一趋势将在未来2-3年内持续加速。",

            f"【{topic}政策分析】各国政府正加快{topic}领域相关政策制定。"
            f"美国、欧盟和中国相继出台支持政策，总投入超过500亿美元。"
            f"政策重点集中在基础设施建设、人才培养和标准制定三个方面。"
            f"专家认为，政策支持将显著降低行业进入门槛。",

            f"【{topic}市场趋势】投资者对{topic}领域的关注度持续上升。"
            f"2026年Q1相关融资事件同比增长40%，平均单笔融资额达到8000万美元。"
            f"二级市场相关概念股市值加权涨幅达到18%。"
            f"机构投资者普遍看好中长期发展前景。",
        ]

        articles = []
        for i, text in enumerate(texts):
            articles.append(Article(
                title=f"[测试] {topic}分析报告 {i+1}",
                url=f"https://test-data.example/{i}",
                source="[测试数据]",
                description=text[:200],
                content=text,
            ))

        logger.info(f"Scout hardcoded fallback: {len(articles)} test articles")
        return ScoutResult(topic=topic, articles=articles, raw_texts=texts)

    async def _execute_search(self, keywords: list[str]) -> list[Article]:
        """执行关键词搜索"""
        all_articles: list[Article] = []
        from_date = datetime.now() - timedelta(days=7)

        for keyword in keywords:
            try:
                articles = await self.news_client.search_everything(
                    query=keyword,
                    from_date=from_date,
                    page_size=10,
                )
                all_articles.extend(articles)
            except NewsAPIError as e:
                logger.error(f"Failed to search keyword '{keyword}': {e}")
                continue

        return all_articles

    async def _refine_keywords(self, topic: str, existing_articles: list[Article]) -> list[str]:
        """基于第一轮结果，让 LLM 调整关键词"""
        try:
            # 构建第一轮结果摘要
            titles = [a.title for a in existing_articles[:10]]
            summary = "\n".join(f"- {t}" for t in titles) if titles else "No results found"

            messages = [
                {
                    "role": "system",
                    "content": "你是一位搜索优化专家。根据初始搜索结果，生成替代关键词以找到更多相关新闻。重点关注现有结果未覆盖的方面。",
                },
                {
                    "role": "user",
                    "content": (
                        f"主题：{topic}\n\n"
                        f"初始搜索结果：\n{summary}\n\n"
                        "请生成 3 个替代搜索关键词，以找到更多相关报道。"
                    ),
                },
            ]

            strategy = await llm_client.extract(
                response_model=SearchStrategy,
                messages=messages,
            )
            return strategy.keywords[:3]

        except Exception as e:
            logger.warning(f"Keyword refinement failed: {e}")
            return [f"{topic} 新闻", f"{topic} 最新动态"]

    def _deduplicate(self, articles: list[Article]) -> list[Article]:
        """按 URL 去重"""
        seen_urls: set[str] = set()
        unique: list[Article] = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique.append(article)
        return unique

    def _extract_article_text(self, article: Article) -> Optional[str]:
        """提取文章文本"""
        # 优先使用 API 返回的 content
        if article.content and len(article.content) > 100:
            return article.content

        # 其次使用 description
        if article.description and len(article.description) > 50:
            return article.description

        # 否则尝试抓取网页
        # 注意: 这里简化处理，实际应该异步抓取网页
        return None

    def generate_search_keywords(self, topic: str) -> list[str]:
        """生成搜索关键词

        根据主题生成相关的搜索关键词。

        Args:
            topic: 主题名称

        Returns:
            关键词列表
        """
        current_year = datetime.now().year
        keywords = [
            topic,
            f"{topic} {current_year}",
            f"{topic} analysis",
            f"{topic} trends",
        ]
        return keywords


# 全局 ScoutNode 实例
scout_node = ScoutNode()
