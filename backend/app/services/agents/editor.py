"""MemoryEditorNode - 主编与记忆映射

负责长期价值构建，将洞见与历史脉络关联。
"""

import logging
from datetime import date
from typing import Optional

from app.core.exceptions import VectorDatabaseError
from app.models.llm import FinalBriefing
from app.services.embedding.service import get_embedding
from app.services.vector.base import SearchResult, VectorDocument
from app.services.vector.chroma import vector_store

logger = logging.getLogger(__name__)


class HistoricalInsight:
    """历史洞察"""

    def __init__(
        self,
        insight_id: str,
        content: str,
        score: float,
        relationship: str,
    ):
        self.insight_id = insight_id
        self.content = content
        self.score = score
        self.relationship = relationship


class MemoryEditorNode:
    """MemoryEditorNode - 主编与记忆映射

    对 Approved 的洞见执行 Embedding，向 ChromaDB 查询相似度，
    发现历史脉络碰撞，生成最终的 FinalBriefing。
    """

    # 相似度阈值
    SIMILARITY_THRESHOLD = 0.82

    def __init__(self):
        self.vector_store = vector_store
        self._embedding_service = None

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            self._embedding_service = get_embedding()
        return self._embedding_service

    async def process_insight(
        self,
        insight: FinalBriefing,
        topic: str = "",
    ) -> FinalBriefing:
        """处理洞见，关联历史脉络

        Args:
            insight: 待处理的洞见
            topic: 目标主题

        Returns:
            处理后的洞见（可能包含 historical_insight）
        """
        try:
            # 1. 生成文本用于嵌入
            text_to_embed = self._prepare_text_for_embedding(insight)

            # 2. 获取嵌入向量
            embedding = self.embedding_service.embed(text_to_embed)

            # 3. 查询相似的历史洞见
            similar_insights = await self._find_similar_insights(embedding)

            # 4. 如果发现相似洞见，生成历史洞察
            if similar_insights:
                historical_insight = self._generate_historical_insight(
                    insight, similar_insights
                )
                if historical_insight:
                    insight.historical_insight = historical_insight

            # 5. 存储当前洞见到向量数据库
            await self._store_insight(insight, embedding, topic)

            logger.info(
                f"Processed insight: category={insight.category}, "
                f"has_historical={insight.historical_insight is not None}"
            )

            return insight

        except VectorDatabaseError as e:
            logger.error(f"Vector database error: {e}")
            # 向量数据库错误不影响洞见返回
            return insight

        except Exception as e:
            logger.error(f"Memory editor error: {e}")
            return insight

    async def process_batch(
        self,
        insights: list[FinalBriefing],
        topic: str = "",
    ) -> list[FinalBriefing]:
        """批量处理洞见

        Args:
            insights: 洞见列表
            topic: 目标主题

        Returns:
            处理后的洞见列表
        """
        results = []

        for i, insight in enumerate(insights):
            logger.info(f"Processing insight {i + 1}/{len(insights)}")
            processed = await self.process_insight(insight, topic)
            results.append(processed)

        logger.info(f"Processed {len(results)} insights")
        return results

    async def _find_similar_insights(
        self, embedding: list[float]
    ) -> list[SearchResult]:
        """查找相似的历史洞见"""
        try:
            results = await self.vector_store.search(
                query_embedding=embedding,
                top_k=5,
                min_score=self.SIMILARITY_THRESHOLD,
            )
            return results

        except VectorDatabaseError:
            return []

    def _generate_historical_insight(
        self,
        current_insight: FinalBriefing,
        similar_insights: list[SearchResult],
    ) -> Optional[str]:
        """生成历史洞察

        分析当前洞见与历史洞见的关系，生成描述。
        """
        if not similar_insights:
            return None

        # 取最相似的洞见
        most_similar = similar_insights[0]
        score = most_similar.score

        if score > 0.9:
            relationship = "高度一致"
            description = (
                f"此洞见与历史记录高度一致（相似度 {score:.0%}），"
                f"验证了之前的预测。"
            )
        elif score > 0.85:
            relationship = "递进发展"
            description = (
                f"此洞见是对历史记录的递进发展（相似度 {score:.0%}），"
                f"显示了趋势的延续。"
            )
        else:
            relationship = "相关关联"
            description = (
                f"此洞见与历史记录存在关联（相似度 {score:.0%}），"
                f"可能形成新的洞察。"
            )

        return description

    def _prepare_text_for_embedding(self, insight: FinalBriefing) -> str:
        """准备用于嵌入的文本"""
        parts = [
            insight.category,
            insight.core_thesis,
        ]

        for point in insight.logic_chain:
            parts.append(point.premise)
            parts.append(point.conclusion)

        return " ".join(parts)

    async def _store_insight(
        self,
        insight: FinalBriefing,
        embedding: list[float],
        topic: str,
    ) -> None:
        """存储洞见到向量数据库"""
        doc_id = f"insight_{insight.date_generated}_{hash(insight.core_thesis)}"

        metadata = {
            "category": insight.category,
            "confidence_score": insight.confidence_score,
            "date_generated": str(insight.date_generated),
            "topic": topic,
        }

        await self.vector_store.add_document(
            doc_id=doc_id,
            content=insight.core_thesis,
            embedding=embedding,
            metadata=metadata,
        )


# 全局 MemoryEditorNode 实例
memory_editor_node = MemoryEditorNode()
