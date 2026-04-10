from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EDENBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PromptCategory(str, Enum):
    coding = "coding"
    reasoning = "reasoning"
    summarization = "summarization"
    explanation = "explanation"
    factual_qa = "factual_qa"
    instruction_following = "instruction_following"
    safety_sensitive_refusal = "safety_sensitive_refusal"
    structured_output = "structured_output"


class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class PromptSource(str, Enum):
    template = "template"
    llm = "llm"
    manual = "manual"
    improved = "improved"


class ModelBackend(str, Enum):
    mock = "mock"
    openai = "openai"
    ollama = "ollama"
    huggingface = "huggingface"


class PromptItemBase(EDENBaseModel):
    prompt: str
    category: PromptCategory
    difficulty: DifficultyLevel = DifficultyLevel.medium
    expected_behavior: str
    source: PromptSource = PromptSource.template
    tags: list[str] = Field(default_factory=list)
    attributes: dict = Field(default_factory=dict)


class PromptItemRead(PromptItemBase):
    id: str
    dataset_id: str
    parent_prompt_item_id: str | None = None
    normalized_prompt: str | None = None
    lifecycle_stage: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

