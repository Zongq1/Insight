"""网页内容提取器

从 HTML 中提取干净的正文内容。
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)


class ContentExtractor:
    """网页内容提取器

    从 HTML 中提取正文内容，剥离广告、导航栏等无关元素。
    """

    # 需要移除的标签
    REMOVE_TAGS = [
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        "iframe",
        "noscript",
        "svg",
        "form",
        "button",
        "input",
        "select",
        "textarea",
    ]

    # 需要移除的 CSS 类名关键词
    REMOVE_CLASS_KEYWORDS = [
        "ad",
        "ads",
        "advertisement",
        "sidebar",
        "menu",
        "nav",
        "footer",
        "header",
        "comment",
        "social",
        "share",
        "related",
        "recommend",
        "popup",
        "modal",
        "banner",
    ]

    # 可能是正文的标签
    CONTENT_TAGS = [
        "article",
        "main",
        "section",
        "div",
        "p",
    ]

    def extract_from_html(self, html: str, url: Optional[str] = None) -> str:
        """从 HTML 提取正文

        Args:
            html: HTML 内容
            url: 页面 URL（用于日志）

        Returns:
            提取的纯文本内容
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, "html.parser")

            # 移除不需要的标签
            self._remove_unwanted_tags(soup)

            # 移除广告等无关元素
            self._remove_ads(soup)

            # 提取正文
            content = self._extract_content(soup)

            # 清理文本
            content = self._clean_text(content)

            if url:
                logger.debug(f"Extracted {len(content)} chars from {url}")

            return content

        except Exception as e:
            logger.error(f"Failed to extract content: {e}")
            return ""

    def _remove_unwanted_tags(self, soup: BeautifulSoup) -> None:
        """移除不需要的标签"""
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

    def _remove_ads(self, soup: BeautifulSoup) -> None:
        """移除广告等无关元素"""
        for tag in soup.find_all(True):
            # 检查 class 属性
            classes = tag.get("class", [])
            if isinstance(classes, str):
                classes = classes.split()

            class_str = " ".join(classes).lower()
            id_str = (tag.get("id") or "").lower()

            # 如果包含广告相关关键词，移除
            for keyword in self.REMOVE_CLASS_KEYWORDS:
                if keyword in class_str or keyword in id_str:
                    tag.decompose()
                    break

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        # 尝试找 article 标签
        article = soup.find("article")
        if article:
            return article.get_text(separator="\n", strip=True)

        # 尝试找 main 标签
        main = soup.find("main")
        if main:
            return main.get_text(separator="\n", strip=True)

        # 尝试找 role="main" 的元素
        main_role = soup.find(attrs={"role": "main"})
        if main_role:
            return main_role.get_text(separator="\n", strip=True)

        # 尝试找最大的文本块
        return self._find_largest_text_block(soup)

    def _find_largest_text_block(self, soup: BeautifulSoup) -> str:
        """找到最大的文本块"""
        best_tag = None
        best_score = 0

        for tag in soup.find_all(self.CONTENT_TAGS):
            # 计算文本长度
            text = tag.get_text(separator=" ", strip=True)
            text_len = len(text)

            # 计算链接密度（链接文本占比）
            links_len = sum(len(a.get_text()) for a in tag.find_all("a"))
            link_density = links_len / max(text_len, 1)

            # 计算得分（文本长度 * (1 - 链接密度)）
            score = text_len * (1 - link_density)

            if score > best_score:
                best_score = score
                best_tag = tag

        if best_tag:
            return best_tag.get_text(separator="\n", strip=True)

        # 如果都没找到，返回 body 的文本
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)

        return soup.get_text(separator="\n", strip=True)

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r"\s+", " ", text)

        # 移除多余换行
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 移除首尾空白
        text = text.strip()

        return text


# 全局内容提取器实例
content_extractor = ContentExtractor()
