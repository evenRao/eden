from app.models.prompt import PromptItem
from app.models.score import QualityScore


DIFFICULTY_ORDER = {"easy": "medium", "medium": "hard", "hard": "hard"}


class PromptImprover:
    """Deterministic prompt rewriter guided by score breakdowns and eval signals."""

    def rewrite(
        self,
        item: PromptItem,
        score: QualityScore,
        low_discriminative_power: bool = False,
    ) -> dict:
        weaknesses: list[str] = []
        improved_prompt = item.prompt.strip()
        improved_expected_behavior = item.expected_behavior.strip()
        new_difficulty = item.difficulty
        action = "rewrite"

        if score.clarity < 0.62:
            weaknesses.append("low_clarity")
            improved_prompt += " State the task explicitly, keep the scope focused, and avoid vague wording."

        if score.specificity < 0.62:
            weaknesses.append("low_specificity")
            if item.category == "structured_output":
                improved_prompt += " Return valid JSON with stable keys: summary, evidence, confidence."
            elif item.category == "coding":
                improved_prompt += " Include function signature, validation logic, and at least two edge cases."
            else:
                improved_prompt += " Include concrete constraints, evaluation criteria, and a precise output format."

        if score.category_fit < 0.58:
            weaknesses.append("weak_category_fit")
            category_prefix = {
                "reasoning": "Reason step by step before the final answer.",
                "summarization": "Provide a concise summary with key facts only.",
                "explanation": "Explain the concept clearly for the intended audience.",
                "factual_qa": "Answer with verified facts and clearly label uncertainty.",
            }.get(item.category, "Align the response style closely to the requested category.")
            improved_prompt = f"{category_prefix} {improved_prompt}"

        if score.diversity_contribution < 0.5:
            weaknesses.append("low_diversity")
            improved_prompt += " Add one non-obvious edge case or failure mode to make this prompt more distinctive."

        if len(item.expected_behavior.split()) < 12:
            weaknesses.append("weak_metadata")
            improved_expected_behavior = (
                f"{item.expected_behavior.strip()} The response should remain accurate, follow the constraints, "
                "surface uncertainty honestly, and demonstrate category-appropriate behavior."
            )

        if low_discriminative_power:
            weaknesses.append("low_discriminative_power")
            action = "increase_difficulty"
            new_difficulty = DIFFICULTY_ORDER.get(item.difficulty, item.difficulty)
            improved_prompt += (
                " Add a stricter constraint, discuss failure modes, and make the answer detailed enough "
                "to separate stronger models from weaker ones."
            )

        reason = (
            "Prompt underperformed on quality heuristics."
            if weaknesses
            else "Prompt did not require deterministic improvement."
        )

        return {
            "prompt": improved_prompt.strip(),
            "expected_behavior": improved_expected_behavior.strip(),
            "difficulty": new_difficulty,
            "weaknesses": weaknesses,
            "action": action,
            "reason": reason,
        }

