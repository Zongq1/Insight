"""RSS 新闻客户端

从国内科技媒体 RSS 订阅源抓取文章。
作为 News API 的替代方案，无需 API Key，国内网络可直接访问。
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.services.agents.scout import Article

logger = logging.getLogger(__name__)

# RSS 源配置（仅保留可用源）
RSS_FEEDS = [
    {
        "name": "36氪",
        "url": "https://36kr.com/feed",
        "category": "科技创业",
    },
]


class RSSClient:
    """RSS 客户端

    支持标准 RSS/Atom 格式和部分站点 API。
    """

    def __init__(self):
        self.timeout = 5.0

    async def fetch_all(self, keywords: list[str] | None = None) -> list[Article]:
        """从所有 RSS 源抓取文章

        Args:
            keywords: 关键词过滤（可选）

        Returns:
            文章列表
        """
        all_articles: list[Article] = []

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for feed in RSS_FEEDS:
                try:
                    if feed.get("type") == "api":
                        articles = await self._fetch_infoq(client, feed)
                    else:
                        articles = await self._fetch_rss(client, feed)
                    all_articles.extend(articles)
                    logger.info(f"RSS [{feed['name']}]: fetched {len(articles)} articles")
                except Exception as e:
                    logger.warning(f"RSS [{feed['name']}] failed: {e}")
                    continue

        # 关键词过滤（仅当关键词数量 > 1 时过滤，单个关键词太宽泛）
        if keywords and len(keywords) > 1:
            all_articles = self._filter_by_keywords(all_articles, keywords)

        logger.info(f"RSS total: {len(all_articles)} articles from {len(RSS_FEEDS)} feeds")
        return all_articles

    async def _fetch_rss(
        self, client: httpx.AsyncClient, feed: dict
    ) -> list[Article]:
        """抓取标准 RSS/Atom 源"""
        response = await client.get(feed["url"])
        response.raise_for_status()
        content = response.text

        return self._parse_rss_xml(content, feed["name"])

    def _parse_rss_xml(self, xml_text: str, source_name: str) -> list[Article]:
        """解析 RSS/Atom XML"""
        articles = []

        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_text)

            # 处理命名空间
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "dc": "http://purl.org/dc/elements/1.1/",
                "content": "http://purl.org/rss/1.0/modules/content/",
            }

            # 尝试 RSS 2.0 格式
            items = root.findall(".//item")
            if not items:
                # 尝试 Atom 格式
                items = root.findall(".//atom:entry", ns)
                if not items:
                    # 尝试无命名空间
                    items = root.findall(".//entry")

            for item in items[:15]:  # 每源最多 15 篇
                title = self._get_text(item, ["title"], ns)
                link = self._get_link(item, ns)
                description = self._get_text(
                    item, ["description", "summary", "atom:summary", "content:encoded"], ns
                )
                pub_date = self._get_text(
                    item, ["pubDate", "dc:date", "atom:published", "atom:updated"], ns
                )

                if title:
                    articles.append(Article(
                        title=title.strip(),
                        url=link or "",
                        source=source_name,
                        published_at=self._parse_date(pub_date),
                        description=self._clean_html(description)[:300] if description else None,
                        content=self._clean_html(description) if description else None,
                    ))

        except Exception as e:
            logger.warning(f"RSS XML parse error: {e}")

        return articles

    def _get_text(self, element, tag_names: list[str], ns: dict) -> Optional[str]:
        """尝试多个标签名获取文本"""
        for tag in tag_names:
            el = element.find(tag, ns) if ":" in tag else element.find(tag)
            if el is not None and el.text:
                return el.text.strip()
        return None

    def _get_link(self, element, ns: dict) -> Optional[str]:
        """获取链接（处理 RSS 和 Atom 两种格式）"""
        # RSS 2.0: <link>
        link = element.find("link")
        if link is not None and link.text:
            return link.text.strip()

        # Atom: <link href="...">
        link = element.find("atom:link", ns)
        if link is not None:
            return link.get("href", "").strip()

        # 无命名空间
        link = element.find("link")
        if link is not None:
            href = link.get("href")
            if href:
                return href.strip()
            if link.text:
                return link.text.strip()

        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None

        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 UTC
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _clean_html(self, text: Optional[str]) -> str:
        """移除 HTML 标签"""
        if not text:
            return ""

        import re
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&\w+;", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    async def _fetch_infoq(
        self, client: httpx.AsyncClient, feed: dict
    ) -> list[Article]:
        """抓取 InfoQ China API"""
        payload = {
            "type": 1,
            "size": 15,
            "id": 0,
        }

        response = await client.post(
            feed["url"],
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("data", []):
            title = item.get("article_title", "")
            summary = item.get("article_summary", "")
            uuid = item.get("uuid", "")

            if title:
                articles.append(Article(
                    title=title,
                    url=f"https://www.infoq.cn/article/{uuid}" if uuid else "",
                    source=feed["name"],
                    description=summary[:300] if summary else None,
                    content=summary if summary else None,
                ))

        return articles

    def _filter_by_keywords(
        self, articles: list[Article], keywords: list[str]
    ) -> list[Article]:
        """按关键词过滤文章"""
        filtered = []
        keywords_lower = [k.lower() for k in keywords]

        for article in articles:
            text = f"{article.title} {article.description or ''}".lower()
            if any(kw in text for kw in keywords_lower):
                filtered.append(article)

        # 如果过滤后太少，返回全部
        if len(filtered) < 3:
            return articles

        return filtered


# 全局实例
rss_client = RSSClient()
