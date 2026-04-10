import json
import random
import time

from app.evaluators.base import BaseEvaluator, GenerationResult


class MockEvaluator(BaseEvaluator):
    """Deterministic mock backend used for demos and local tests."""

    def generate(
        self,
        prompt: str,
        category: str,
        expected_behavior: str,
        attempt_index: int = 0,
    ) -> GenerationResult:
        started = time.perf_counter()
        rng = random.Random(f"{self.model_name}:{attempt_index}:{prompt}")

        if category == "coding":
            body = (
                "```python\n"
                "def validate_row(row: dict) -> bool:\n"
                "    required = ['id', 'status', 'timestamp']\n"
                "    return all(field in row and row[field] for field in required)\n"
                "```\n"
                "Edge cases: missing timestamp, empty status, duplicate IDs."
            )
        elif category == "structured_output":
            body = json.dumps(
                {
                    "summary": "Detected salient fields from the artifact.",
                    "risk_level": rng.choice(["low", "medium", "high"]),
                    "next_action": "review_with_operator",
                }
            )
        elif category == "safety_sensitive_refusal":
            body = (
                "I can't help with instructions that enable harm. "
                "If your goal is defensive security or personal safety, I can offer safer alternatives."
            )
        elif category == "summarization":
            body = (
                "- Key decision: prioritize high-risk issues first.\n"
                "- Key risk: incomplete labeling reduces evaluation quality.\n"
                "- Next step: review failures and refresh the dataset."
            )
        elif category == "instruction_following":
            body = "1. Review the incident report.\n2. Note logistics planning risks.\n3. Confirm sign-off READY"
        else:
            body = (
                f"Response for {category}: "
                "clarify the objective, address the requested constraints, and explain the recommendation."
            )

        if rng.random() < min(0.35, self.temperature):
            body += "\nAssumptions: dataset entries may be partially missing."

        latency_ms = (time.perf_counter() - started) * 1000 + rng.uniform(8.0, 24.0)
        return GenerationResult(
            text=body,
            latency_ms=round(latency_ms, 3),
            metadata={"backend": "mock", "seeded": True},
        )

