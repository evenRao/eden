from datetime import datetime

from pydantic import Field

from app.schemas.common import (
    DifficultyLevel,
    EDENBaseModel,
    PromptCategory,
    PromptItemRead,
)


class GenerateDatasetRequest(EDENBaseModel):
    dataset_name: str
    description: str | None = None
    num_items: int = Field(default=24, ge=1, le=500)
    categories: list[PromptCategory] = Field(default_factory=list)
    difficulties: list[DifficultyLevel] = Field(default_factory=list)
    seed: int = 42
    llm_assisted: bool = False
    tags: list[str] = Field(default_factory=list)


class CleanDatasetRequest(EDENBaseModel):
    dataset_id: str
    semantic_threshold: float = Field(default=0.92, ge=0.5, le=0.999)
    remove_low_information: bool = True


class ScoreDatasetRequest(EDENBaseModel):
    dataset_id: str


class DatasetRead(EDENBaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    source: str
    tags: list[str]
    dataset_metadata: dict
    created_at: datetime
    updated_at: datetime


class DatasetDetail(DatasetRead):
    prompt_items: list[PromptItemRead] = Field(default_factory=list)


class DatasetSummaryResponse(EDENBaseModel):
    dataset: DatasetRead
    item_count: int


class DatasetStageResponse(EDENBaseModel):
    dataset_id: str
    dataset_name: str
    status: str
    item_count: int
    artifacts: list[str] = Field(default_factory=list)
    message: str

