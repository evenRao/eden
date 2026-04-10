from typing import Optional

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.ids import generate_uuid


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="generated", nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="template", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    dataset_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    prompt_items = relationship(
        "PromptItem", back_populates="dataset", cascade="all, delete-orphan"
    )
    evaluation_runs = relationship(
        "EvaluationRun", back_populates="dataset", cascade="all, delete-orphan"
    )
    improvement_records = relationship(
        "ImprovementRecord", back_populates="dataset", cascade="all, delete-orphan"
    )
    metric_snapshots = relationship(
        "MetricSnapshot", back_populates="dataset", cascade="all, delete-orphan"
    )
