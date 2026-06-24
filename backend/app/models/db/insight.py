"""Insight ORM 模型"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin


class Insight(Base, TimestampMixin):
    """洞见表"""

    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    core_thesis: Mapped[str] = mapped_column(Text, nullable=False)
    logic_chain: Mapped[dict] = mapped_column(JSON, nullable=False)
    historical_insight: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sources: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    date_generated: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, category='{self.category}', date={self.date_generated})>"


class InsightVersion(Base, TimestampMixin):
    """洞见版本表

    记录洞见的修订历史。
    """

    __tablename__ = "insight_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    core_thesis: Mapped[str] = mapped_column(Text, nullable=False)
    logic_chain: Mapped[dict] = mapped_column(JSON, nullable=False)
    historical_insight: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sources: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<InsightVersion(insight_id={self.insight_id}, version={self.version})>"
