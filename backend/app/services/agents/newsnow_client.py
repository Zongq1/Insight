"""NewsNow API 客户端

从 NewsNow 公共 API 获取多平台热点数据。
免费、国内直连、无需 API Key。

API 格式: GET https://newsnow.busiyi.world/api/s?id={platform}&latest
响应: {"status": "success"|"cache", "items": [{"title": str, "url": str, ...}]}
"""

import asyncio
import logging
from typing import Optional

import httpx

from app.services.agents.scout import Article

logger = logging.getLogger(__name__)

# 可用平台列表
PLATFORMS = {
    "weibo": "微博",
    "zhihu": "知乎",
    "toutiao": "头条",
    "baidu": "百度",
    "bilibili-hot-search": "B站",
    "douyin": "抖音",
    "tieba": "贴吧",
    "cls-hot": "财联社",
    "ifeng": "凤凰网",
    "thepaper": "澎湃",
    "wallstreetcn-hot": "华尔街见闻",
}

# 默认抓取平台（覆盖面广、数据质量高）
DEFAULT_PLATFORMS = ["weibo", "zhihu", "toutiao"]

BASE_URL = "https://newsnow.busiyi.world/api/s"


class NewsNowClient:
    """NewsNow API 客户端

    异步抓取多平台热点新闻，支持并行请求和自动重试。
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def fetch_platform(
        self,
        platform_id: str,
        client: httpx.AsyncClient,
        max_retries: int = 2,
    ) -> list[Article]:
        """抓取单个平台的热点数据

        Args:
            platform_id: 平台 ID（如 "weibo", "zhihu"）
            client: httpx 异步客户端
            max_retries: 最大重试次数

        Returns:
            Article 列表
        """
        url = f"{BASE_URL}?id={platform_id}&latest"
        platform_name = PLATFORMS.get(platform_id, platform_id)

        for attempt in range(max_retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                status = data.get("status", "")
                if status not in ("success", "cache"):
                    logger.warning(f"NewsNow [{platform_id}] unexpected status: {status}")
                    if attempt < max_retries:
                        await asyncio.sleep(1)
                        continue
                    return []

                items = data.get("items", [])
                articles = []
                for item in items:
                    title = item.get("title")
                    if not title or isinstance(title, float):
                        continue
                    title = str(title).strip()
                    if not title:
                        continue

                    articles.append(Article(
                        title=title,
                        url=item.get("url", ""),
                        source=platform_name,
                        description=title,  # 热点标题即描述
                        content=title,
                    ))

                logger.info(f"NewsNow [{platform_name}]: fetched {len(articles)} items")
                return articles

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"NewsNow [{platform_id}] attempt {attempt+1} failed: {e}")
                    await asyncio.sleep(1)
                else:
                    logger.error(f"NewsNow [{platform_id}] all retries failed: {e}")
                    return []

        return []

    async def fetch_multiple(
        self,
        platforms: list[str] | None = None,
        keywords: list[str] | None = None,
    ) -> list[Article]:
        """并行抓取多个平台，可选关键词过滤

        Args:
            platforms: 平台 ID 列表，默认使用 DEFAULT_PLATFORMS
            keywords: 关键词过滤（可选，标题包含任一关键词即保留）

        Returns:
            去重后的 Article 列表
        """
        if platforms is None:
            platforms = DEFAULT_PLATFORMS

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
        ) as client:
            tasks = [self.fetch_platform(pid, client) for pid in platforms]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        all_articles: list[Article] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"NewsNow [{platforms[i]}] exception: {result}")
            elif isinstance(result, list):
                all_articles.extend(result)

        # 去重
        seen_titles: set[str] = set()
        unique: list[Article] = []
        for article in all_articles:
            key = article.title.strip()
            if key not in seen_titles:
                seen_titles.add(key)
                unique.append(article)

        # 关键词过滤（如果有多个关键词）
        if keywords and len(keywords) > 1:
            unique = self._filter_by_keywords(unique, keywords)

        logger.info(f"NewsNow total: {len(unique)} unique articles from {len(platforms)} platforms")
        return unique

    def _filter_by_keywords(
        self, articles: list[Article], keywords: list[str]
    ) -> list[Article]:
        """按关键词过滤文章（标题包含任一关键词即保留）"""
        keywords_lower = [k.lower() for k in keywords]
        filtered = []
        for article in articles:
            title_lower = article.title.lower()
            if any(kw in title_lower for kw in keywords_lower):
                filtered.append(article)

        # 如果过滤后太少，返回全部
        if len(filtered) < 3:
            return articles
        return filtered


# 全局实例
newsnow_client = NewsNowClient()
