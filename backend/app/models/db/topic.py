"""Topic ORM 模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin


class Topic(Base, TimestampMixin):
    """主题表"""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    keywords: Mapped[dict] = mapped_column(JSON, nullable=False)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, name='{self.name}')>"


class TopicInsight(Base, TimestampMixin):
    """主题-洞见关联表"""

    __tablename__ = "topic_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    insight_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    relevance_score: Mapped[float] = mapped_column(default=0.0, nullable=False)

    def __repr__(self) -> str:
        return f"<TopicInsight(topic_id={self.topic_id}, insight_id={self.insight_id})>"
