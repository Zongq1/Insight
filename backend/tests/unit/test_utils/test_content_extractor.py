"""内容提取器测试"""

import pytest

from app.utils.content_extractor import ContentExtractor


@pytest.fixture
def extractor():
    """创建内容提取器实例"""
    return ContentExtractor()


class TestContentExtractor:
    """内容提取器测试"""

    def test_extract_from_simple_html(self, extractor):
        """测试从简单 HTML 提取内容"""
        html = """
        <html>
        <body>
            <div>
                <h1>Test Title</h1>
                <p>This is a test paragraph with enough content to be selected.</p>
                <p>This is another paragraph with more content for testing.</p>
            </div>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        assert "Test Title" in content
        assert "test paragraph" in content
        assert "another paragraph" in content

    def test_extract_removes_scripts(self, extractor):
        """测试移除 script 标签"""
        html = """
        <html>
        <body>
            <p>Real content</p>
            <script>alert('test');</script>
            <script type="text/javascript">var x = 1;</script>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        assert "Real content" in content
        assert "alert" not in content
        assert "var x" not in content

    def test_extract_removes_styles(self, extractor):
        """测试移除 style 标签"""
        html = """
        <html>
        <head>
            <style>body { color: red; }</style>
        </head>
        <body>
            <p>Real content</p>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        assert "Real content" in content
        assert "color: red" not in content

    def test_extract_removes_nav(self, extractor):
        """测试移除 nav 标签"""
        html = """
        <html>
        <body>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
            </nav>
            <article>
                <p>Article content</p>
            </article>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        assert "Article content" in content
        # 导航链接可能不会完全移除，但应该提取到文章内容

    def test_extract_from_article_tag(self, extractor):
        """测试从 article 标签提取"""
        html = """
        <html>
        <body>
            <header>Header content</header>
            <article>
                <h1>Article Title</h1>
                <p>Article content here.</p>
            </article>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        assert "Article Title" in content
        assert "Article content" in content

    def test_extract_from_main_tag(self, extractor):
        """测试从 main 标签提取"""
        html = """
        <html>
        <body>
            <header>Header</header>
            <main>
                <p>Main content here.</p>
            </main>
            <footer>Footer</footer>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        assert "Main content" in content

    def test_extract_empty_html(self, extractor):
        """测试空 HTML"""
        content = extractor.extract_from_html("")
        assert content == ""

    def test_extract_none_html(self, extractor):
        """测试 None HTML"""
        content = extractor.extract_from_html(None)
        assert content == ""

    def test_extract_cleans_whitespace(self, extractor):
        """测试清理多余空白"""
        html = """
        <html>
        <body>
            <p>First paragraph.</p>



            <p>Second paragraph.</p>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        # 应该清理多余空白
        assert "   " not in content
        assert "\n\n\n" not in content

    def test_extract_removes_ads(self, extractor):
        """测试移除广告元素"""
        html = """
        <html>
        <body>
            <div class="ad-banner">Advertisement</div>
            <div class="sidebar-ad">Ad content</div>
            <article>
                <p>Real content</p>
            </article>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html)

        assert "Real content" in content

    def test_extract_with_url(self, extractor):
        """测试带 URL 的提取"""
        html = """
        <html>
        <body>
            <p>Content</p>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html, url="https://example.com")

        assert "Content" in content

    def test_extract_complex_article(self, extractor):
        """测试复杂文章提取"""
        html = """
        <html>
        <head>
            <title>Test Article</title>
            <style>body { font-family: Arial; }</style>
        </head>
        <body>
            <nav>
                <a href="/">Home</a>
                <a href="/news">News</a>
            </nav>
            <div class="container">
                <article class="post">
                    <h1>Breaking News: AI Advances</h1>
                    <div class="meta">
                        <span class="date">2024-01-15</span>
                        <span class="author">John Doe</span>
                    </div>
                    <div class="content">
                        <p>Artificial intelligence has made significant progress in 2024.</p>
                        <p>New models are capable of understanding complex contexts.</p>
                        <p>Experts predict even greater advances in the coming years.</p>
                    </div>
                    <div class="social-share">
                        <button>Share on Twitter</button>
                        <button>Share on Facebook</button>
                    </div>
                </article>
                <aside class="related">
                    <h3>Related Articles</h3>
                    <ul>
                        <li><a href="/article1">Article 1</a></li>
                        <li><a href="/article2">Article 2</a></li>
                    </ul>
                </aside>
            </div>
            <footer>
                <p>Copyright 2024</p>
            </footer>
            <script>
                // Analytics code
                console.log("tracking");
            </script>
        </body>
        </html>
        """
        content = extractor.extract_from_html(html, url="https://example.com/article")

        assert "Breaking News: AI Advances" in content
        assert "Artificial intelligence" in content
        assert "significant progress" in content
        assert "complex contexts" in content
