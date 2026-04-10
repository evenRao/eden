from typing import Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.ids import generate_uuid


class PromptItem(Base, TimestampMixin):
    __tablename__ = "prompt_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_prompt_item_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("prompt_items.id", ondelete="SET NULL"), nullable=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="template")
    lifecycle_stage: Mapped[str] = mapped_column(
        String(50), nullable=False, default="generated"
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    dataset = relationship("Dataset", back_populates="prompt_items")
    parent = relationship("PromptItem", remote_side=[id], back_populates="children")
    children = relationship("PromptItem", back_populates="parent")
    quality_scores = relationship(
        "QualityScore", back_populates="prompt_item", cascade="all, delete-orphan"
    )
    model_outputs = relationship("ModelOutput", back_populates="prompt_item")
    original_improvements = relationship(
        "ImprovementRecord",
        foreign_keys="ImprovementRecord.original_prompt_item_id",
        back_populates="original_prompt",
    )
    improved_improvements = relationship(
        "ImprovementRecord",
        foreign_keys="ImprovementRecord.improved_prompt_item_id",
        back_populates="improved_prompt",
    )
