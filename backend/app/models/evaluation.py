from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.ids import generate_uuid


class EvaluationRun(Base, TimestampMixin):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_name: Mapped[str] = mapped_column(String(255), nullable=False)
    backend: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    repeats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aggregate_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    dataset = relationship("Dataset", back_populates="evaluation_runs")
    model_outputs = relationship(
        "ModelOutput", back_populates="evaluation_run", cascade="all, delete-orphan"
    )


class ModelOutput(Base, TimestampMixin):
    __tablename__ = "model_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt_item_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    response_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    structured_output_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    response_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    length_appropriateness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    refusal_correctness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_behavior_overlap: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    heuristic_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    consistency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evaluation_run = relationship("EvaluationRun", back_populates="model_outputs")
    prompt_item = relationship("PromptItem", back_populates="model_outputs")
