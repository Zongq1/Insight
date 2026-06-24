"""Token 使用记录 ORM 模型"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin


class TokenUsageRecord(TimestampMixin, Base):
    """Token 使用记录表"""

    __tablename__ = "token_usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    input_cost: Mapped[float] = mapped_column(Float, nullable=False)
    output_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )
