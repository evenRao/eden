from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "E.D.E.N."
    env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite:///./eden.db"
    log_level: str = "INFO"
    export_artifacts: bool = True
    default_generation_model: str = "mock"
    similarity_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.92
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    hf_model: str = "distilgpt2"
    scoring_version: str = "v1"
    improvement_version: str = "v1"
    random_seed: int = 42
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[3]
    )

    model_config = SettingsConfigDict(
        env_prefix="EDEN_",
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        extra="ignore",
    )

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def evaluation_dir(self) -> Path:
        return self.project_root / "evaluation"

    @property
    def logs_dir(self) -> Path:
        return self.project_root / "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()

