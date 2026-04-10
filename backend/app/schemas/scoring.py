from datetime import datetime

from pydantic import Field

from app.schemas.common import EDENBaseModel


class QualityScoreRead(EDENBaseModel):
    id: str
    prompt_item_id: str
    overall_score: float
    clarity: float
    specificity: float
    usefulness: float
    inverse_ambiguity: float
    diversity_contribution: float
    category_fit: float
    semantic_novelty: float
    lexical_complexity: float
    breakdown: dict
    explanations: list[str] = Field(default_factory=list)
    scoring_version: str
    created_at: datetime
    updated_at: datetime


class ScoreDatasetResponse(EDENBaseModel):
    dataset_id: str
    average_quality_score: float
    score_count: int
    item_scores: list[QualityScoreRead] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)

