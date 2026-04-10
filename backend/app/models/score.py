from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.ids import generate_uuid


class QualityScore(Base, TimestampMixin):
    __tablename__ = "quality_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    prompt_item_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    clarity: Mapped[float] = mapped_column(Float, nullable=False)
    specificity: Mapped[float] = mapped_column(Float, nullable=False)
    usefulness: Mapped[float] = mapped_column(Float, nullable=False)
    inverse_ambiguity: Mapped[float] = mapped_column(Float, nullable=False)
    diversity_contribution: Mapped[float] = mapped_column(Float, nullable=False)
    category_fit: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_novelty: Mapped[float] = mapped_column(Float, nullable=False)
    lexical_complexity: Mapped[float] = mapped_column(Float, nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    explanations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(30), nullable=False, default="v1")

    prompt_item = relationship("PromptItem", back_populates="quality_scores")

