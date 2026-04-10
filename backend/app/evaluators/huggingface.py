import time
from functools import cached_property

from app.evaluators.base import BaseEvaluator, GenerationResult


class HuggingFaceEvaluator(BaseEvaluator):
    @cached_property
    def _pipeline(self):  # type: ignore[no-untyped-def]
        from transformers import pipeline

        return pipeline("text-generation", model=self.model_name)

    def generate(
        self,
        prompt: str,
        category: str,
        expected_behavior: str,
        attempt_index: int = 0,
    ) -> GenerationResult:
        started = time.perf_counter()
        try:
            outputs = self._pipeline(
                prompt,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=self.temperature > 0,
            )
            text = outputs[0]["generated_text"][len(prompt) :].strip()
            return GenerationResult(
                text=text,
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                metadata={"backend": "huggingface"},
            )
        except Exception as exc:
            return GenerationResult(
                text="",
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                metadata={"backend": "huggingface"},
                failure=True,
                error_message=str(exc),
            )

