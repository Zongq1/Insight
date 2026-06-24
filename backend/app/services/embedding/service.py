"""嵌入向量服务

提供文本嵌入功能，支持多种后端：
- sentence-transformers (本地模型)
- mock (测试/开发用)
"""

import hashlib
import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService(ABC):
    """嵌入服务抽象基类"""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """单条文本嵌入"""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量文本嵌入"""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """嵌入向量维度"""
        ...


class SentenceTransformerEmbedding(EmbeddingService):
    """基于 sentence-transformers 的嵌入服务"""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded: dimension={self._dimension}")

        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )

    def embed(self, text: str) -> list[float]:
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbedding(EmbeddingService):
    """模拟嵌入服务（用于测试和开发）

    使用文本 hash 生成确定性伪向量。
    """

    def __init__(self, dim: int = 128):
        self._dimension = dim

    def embed(self, text: str) -> list[float]:
        hash_obj = hashlib.md5(text.encode("utf-8"))
        hash_hex = hash_obj.hexdigest()

        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i : i + 2], 16) / 255.0
            embedding.append(val)

        # 填充到目标维度
        while len(embedding) < self._dimension:
            embedding.append(0.0)

        return embedding[: self._dimension]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务实例

    优先使用 sentence-transformers，不可用时回退到 mock。
    """
    model_name = settings.EMBEDDING_MODEL

    # 如果配置为 mock，直接返回 mock
    if model_name.lower() == "mock":
        logger.info("Using mock embedding service")
        return MockEmbedding()

    try:
        return SentenceTransformerEmbedding(model_name)
    except ImportError:
        logger.warning(
            f"sentence-transformers not available, falling back to mock embedding"
        )
        return MockEmbedding()


# 全局嵌入服务实例（延迟初始化）
_embedding_service: EmbeddingService | None = None


def get_embedding() -> EmbeddingService:
    """获取全局嵌入服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = get_embedding_service()
    return _embedding_service
