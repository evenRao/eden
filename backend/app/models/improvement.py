from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.ids import generate_uuid


class ImprovementRecord(Base, TimestampMixin):
    __tablename__ = "improvement_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_prompt_item_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_items.id", ondelete="CASCADE"), nullable=False
    )
    improved_prompt_item_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("prompt_items.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score_before: Mapped[float] = mapped_column(Float, nullable=False)
    score_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    analysis: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    dataset = relationship("Dataset", back_populates="improvement_records")
    original_prompt = relationship(
        "PromptItem",
        foreign_keys=[original_prompt_item_id],
        back_populates="original_improvements",
    )
    improved_prompt = relationship(
        "PromptItem",
        foreign_keys=[improved_prompt_item_id],
        back_populates="improved_improvements",
    )
