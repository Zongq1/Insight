"""嵌入服务测试

测试 EmbeddingService 的功能。
"""

import pytest

from app.services.embedding.service import (
    MockEmbedding,
    get_embedding_service,
)


class TestMockEmbedding:
    """MockEmbedding 测试"""

    def test_init_default_dimension(self):
        """测试默认维度"""
        service = MockEmbedding()
        assert service.dimension == 128

    def test_init_custom_dimension(self):
        """测试自定义维度"""
        service = MockEmbedding(dim=256)
        assert service.dimension == 256

    def test_embed_returns_correct_dimension(self):
        """测试嵌入维度正确"""
        service = MockEmbedding(dim=128)
        result = service.embed("test text")
        assert len(result) == 128

    def test_embed_values_in_range(self):
        """测试嵌入值在 [0, 1] 范围内"""
        service = MockEmbedding()
        result = service.embed("test text")
        assert all(0.0 <= v <= 1.0 for v in result)

    def test_embed_deterministic(self):
        """测试确定性：相同输入产生相同输出"""
        service = MockEmbedding()
        result1 = service.embed("hello world")
        result2 = service.embed("hello world")
        assert result1 == result2

    def test_embed_different_texts(self):
        """测试不同文本产生不同向量"""
        service = MockEmbedding()
        result1 = service.embed("hello")
        result2 = service.embed("world")
        assert result1 != result2

    def test_embed_chinese_text(self):
        """测试中文文本嵌入"""
        service = MockEmbedding()
        result = service.embed("这是一段中文文本")
        assert len(result) == 128

    def test_embed_empty_text(self):
        """测试空文本嵌入"""
        service = MockEmbedding()
        result = service.embed("")
        assert len(result) == 128

    def test_embed_batch(self):
        """测试批量嵌入"""
        service = MockEmbedding()
        texts = ["hello", "world", "test"]
        results = service.embed_batch(texts)
        assert len(results) == 3
        assert all(len(r) == 128 for r in results)

    def test_embed_batch_empty(self):
        """测试空批量嵌入"""
        service = MockEmbedding()
        results = service.embed_batch([])
        assert results == []

    def test_embed_batch_consistency(self):
        """测试批量和单条一致性"""
        service = MockEmbedding()
        texts = ["hello", "world"]
        batch_results = service.embed_batch(texts)
        single_results = [service.embed(t) for t in texts]
        assert batch_results == single_results


class TestGetEmbeddingService:
    """get_embedding_service 测试"""

    def test_returns_mock_for_mock_config(self):
        """测试 mock 配置返回 MockEmbedding"""
        service = get_embedding_service()
        # 在没有 sentence-transformers 的环境中应该返回 mock
        assert isinstance(service, MockEmbedding)

    def test_service_has_embed_method(self):
        """测试服务有 embed 方法"""
        service = get_embedding_service()
        assert hasattr(service, "embed")
        assert callable(service.embed)

    def test_service_has_embed_batch_method(self):
        """测试服务有 embed_batch 方法"""
        service = get_embedding_service()
        assert hasattr(service, "embed_batch")
        assert callable(service.embed_batch)

    def test_service_has_dimension_property(self):
        """测试服务有 dimension 属性"""
        service = get_embedding_service()
        assert hasattr(service, "dimension")
        assert isinstance(service.dimension, int)
        assert service.dimension > 0
