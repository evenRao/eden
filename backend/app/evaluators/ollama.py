import time

import httpx

from app.core.config import get_settings
from app.evaluators.base import BaseEvaluator, GenerationResult


class OllamaEvaluator(BaseEvaluator):
    def __init__(self, model_name: str, temperature: float = 0.2, max_tokens: int = 256):
        super().__init__(model_name, temperature, max_tokens)
        self.settings = get_settings()

    def generate(
        self,
        prompt: str,
        category: str,
        expected_behavior: str,
        attempt_index: int = 0,
    ) -> GenerationResult:
        started = time.perf_counter()
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return GenerationResult(
                text=data.get("response", ""),
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                metadata={"backend": "ollama", "raw": data},
            )
        except Exception as exc:
            return GenerationResult(
                text="",
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                metadata={"backend": "ollama"},
                failure=True,
                error_message=str(exc),
            )

