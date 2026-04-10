from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GenerationResult:
    text: str
    latency_ms: float
    metadata: dict = field(default_factory=dict)
    failure: bool = False
    error_message: str | None = None


class BaseEvaluator(ABC):
    def __init__(self, model_name: str, temperature: float = 0.2, max_tokens: int = 256):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def generate(
        self,
        prompt: str,
        category: str,
        expected_behavior: str,
        attempt_index: int = 0,
    ) -> GenerationResult:
        """Generate a response for a prompt item."""

