from datetime import datetime

from pydantic import Field

from app.schemas.common import EDENBaseModel, ModelBackend


class ModelConfig(EDENBaseModel):
    backend: ModelBackend = ModelBackend.mock
    model_name: str = "eden-mock-001"
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=256, ge=32, le=4096)


class EvaluateDatasetRequest(EDENBaseModel):
    dataset_id: str
    models: list[ModelConfig] = Field(default_factory=list)
    repeats: int = Field(default=1, ge=1, le=5)
    run_name: str | None = None
    notes: str | None = None


class ModelOutputRead(EDENBaseModel):
    id: str
    evaluation_run_id: str
    prompt_item_id: str
    attempt_index: int
    response_text: str
    latency_ms: float
    response_length: int
    failure: bool
    structured_output_valid: bool | None = None
    response_completeness: float
    length_appropriateness: float
    refusal_correctness: float
    expected_behavior_overlap: float
    heuristic_quality: float
    consistency_score: float | None = None
    evaluator_notes: str | None = None
    raw_metadata: dict
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class EvaluationRunRead(EDENBaseModel):
    id: str
    dataset_id: str
    run_name: str
    backend: str
    model_name: str
    repeats: int
    status: str
    notes: str | None = None
    aggregate_metrics: dict
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_outputs: list[ModelOutputRead] = Field(default_factory=list)


class EvaluateDatasetResponse(EDENBaseModel):
    dataset_id: str
    run_ids: list[str] = Field(default_factory=list)
    evaluations: list[EvaluationRunRead] = Field(default_factory=list)

