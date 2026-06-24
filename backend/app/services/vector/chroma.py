"""ChromaDB 向量数据库实现

基于 ChromaDB 的向量数据库实现，支持 HNSW 参数调优和延迟监控。
"""

import logging
import time
from typing import Any, Optional

from app.config import settings
from app.core.exceptions import VectorDatabaseError
from app.services.vector.base import SearchResult, VectorDocument, VectorStore

logger = logging.getLogger(__name__)

# 延迟告警阈值 (ms)
LATENCY_WARN_THRESHOLD_MS = 200


class ChromaVectorStore(VectorStore):
    """ChromaDB 向量数据库实现"""

    def __init__(self, collection_name: str = "insights"):
        """初始化 ChromaDB

        Args:
            collection_name: 集合名称
        """
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            # 创建持久化客户端
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

            # 获取或创建集合（HNSW 参数调优）
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:M": 16,
                    "hnsw:construction_ef": 200,
                    "hnsw:search_ef": 128,
                },
            )

            logger.info(
                f"ChromaDB initialized: collection={collection_name}, "
                f"count={self.collection.count()}"
            )

        except ImportError:
            logger.error("chromadb not installed")
            raise VectorDatabaseError("chromadb not installed")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise VectorDatabaseError(f"Failed to initialize ChromaDB: {e}")

    async def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """添加文档到 ChromaDB"""
        try:
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata or {}],
            )
            logger.debug(f"Added document: {doc_id}")

        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            raise VectorDatabaseError(f"Failed to add document: {e}")

    async def add_documents(self, documents: list[VectorDocument]) -> None:
        """批量添加文档"""
        if not documents:
            return

        try:
            self.collection.add(
                ids=[doc.id for doc in documents],
                documents=[doc.content for doc in documents],
                embeddings=[doc.embedding for doc in documents],
                metadatas=[doc.metadata for doc in documents],
            )
            logger.info(f"Added {len(documents)} documents")

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise VectorDatabaseError(f"Failed to add documents: {e}")

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """搜索相似文档（带延迟监控）"""
        start_time = time.monotonic()
        try:
            # ChromaDB 使用距离，需要转换为相似度
            # cosine distance = 1 - cosine similarity
            max_distance = 1.0 - min_score

            kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
            }

            if filter_metadata:
                kwargs["where"] = filter_metadata

            results = self.collection.query(**kwargs)

            search_results = []
            if results and results["ids"]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # 转换距离为相似度
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = 1.0 - distance

                    if score >= min_score:
                        doc = VectorDocument(
                            id=doc_id,
                            content=results["documents"][0][i] if results["documents"] else "",
                            metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        )
                        search_results.append(
                            SearchResult(document=doc, score=score)
                        )

            elapsed_ms = (time.monotonic() - start_time) * 1000
            if elapsed_ms > LATENCY_WARN_THRESHOLD_MS:
                logger.warning(
                    f"Vector search slow: {elapsed_ms:.0f}ms "
                    f"(threshold={LATENCY_WARN_THRESHOLD_MS}ms, results={len(search_results)})"
                )
            else:
                logger.debug(f"Vector search: {elapsed_ms:.1f}ms, {len(search_results)} results")

            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise VectorDatabaseError(f"Search failed: {e}")

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        try:
            results = self.collection.get(ids=[doc_id])

            if results and results["ids"]:
                return VectorDocument(
                    id=results["ids"][0],
                    content=results["documents"][0] if results["documents"] else "",
                    metadata=results["metadatas"][0] if results["metadatas"] else {},
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise VectorDatabaseError(f"Failed to get document: {e}")

    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise VectorDatabaseError(f"Failed to delete document: {e}")

    async def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """更新文档"""
        try:
            # 获取现有文档
            existing = await self.get_document(doc_id)
            if not existing:
                return False

            # 更新字段
            update_kwargs = {
                "ids": [doc_id],
                "documents": [content or existing.content],
                "embeddings": [embedding or existing.embedding],
                "metadatas": [metadata or existing.metadata],
            }

            self.collection.update(**update_kwargs)
            logger.debug(f"Updated document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise VectorDatabaseError(f"Failed to update document: {e}")

    async def count(self) -> int:
        """统计文档数量"""
        return self.collection.count()

    async def exists(self, doc_id: str) -> bool:
        """检查文档是否存在"""
        try:
            results = self.collection.get(ids=[doc_id])
            return bool(results and results["ids"])

        except Exception:
            return False


# 全局 ChromaDB 实例
vector_store = ChromaVectorStore()
