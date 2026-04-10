from datetime import datetime

from pydantic import Field

from app.schemas.common import EDENBaseModel


class ImproveDatasetRequest(EDENBaseModel):
    dataset_id: str
    quality_threshold: float = Field(default=0.62, ge=0.0, le=1.0)
    max_candidates: int = Field(default=10, ge=1, le=200)
    prefer_model_feedback: bool = True


class ImprovementRecordRead(EDENBaseModel):
    id: str
    dataset_id: str
    original_prompt_item_id: str
    improved_prompt_item_id: str | None = None
    action: str
    reason: str
    accepted: bool
    score_before: float
    score_after: float | None = None
    analysis: dict
    created_at: datetime
    updated_at: datetime


class ImproveDatasetResponse(EDENBaseModel):
    dataset_id: str
    attempted: int
    accepted: int
    improvements: list[ImprovementRecordRead] = Field(default_factory=list)

