"""向量数据库抽象层

定义向量数据库的通用接口，便于未来迁移。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class VectorDocument(BaseModel):
    """向量文档"""

    id: str = Field(..., description="文档唯一标识")
    content: str = Field(..., description="文档内容")
    embedding: list[float] = Field(default_factory=list, description="向量嵌入")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class SearchResult(BaseModel):
    """搜索结果"""

    document: VectorDocument = Field(..., description="匹配的文档")
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数")


class VectorStore(ABC):
    """向量数据库抽象基类"""

    @abstractmethod
    async def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """添加文档到向量数据库

        Args:
            doc_id: 文档唯一标识
            content: 文档内容
            embedding: 向量嵌入
            metadata: 元数据
        """
        pass

    @abstractmethod
    async def add_documents(self, documents: list[VectorDocument]) -> None:
        """批量添加文档

        Args:
            documents: 文档列表
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """搜索相似文档

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            min_score: 最小相似度分数
            filter_metadata: 元数据过滤条件

        Returns:
            搜索结果列表
        """
        pass

    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """获取文档

        Args:
            doc_id: 文档唯一标识

        Returns:
            文档或 None
        """
        pass

    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档

        Args:
            doc_id: 文档唯一标识

        Returns:
            是否成功删除
        """
        pass

    @abstractmethod
    async def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """更新文档

        Args:
            doc_id: 文档唯一标识
            content: 新内容
            embedding: 新向量
            metadata: 新元数据

        Returns:
            是否成功更新
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """统计文档数量

        Returns:
            文档总数
        """
        pass

    @abstractmethod
    async def exists(self, doc_id: str) -> bool:
        """检查文档是否存在

        Args:
            doc_id: 文档唯一标识

        Returns:
            是否存在
        """
        pass
