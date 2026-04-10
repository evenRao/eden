import time

from app.core.config import get_settings
from app.evaluators.base import BaseEvaluator, GenerationResult


class OpenAIEvaluator(BaseEvaluator):
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
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.openai_api_key)
            completion = client.responses.create(
                model=self.model_name,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are evaluating prompt quality for an LLM dataset. "
                            "Respond faithfully and concisely."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            text = completion.output_text
            return GenerationResult(
                text=text,
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                metadata={"backend": "openai", "response_id": completion.id},
            )
        except Exception as exc:
            return GenerationResult(
                text="",
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                metadata={"backend": "openai"},
                failure=True,
                error_message=str(exc),
            )

