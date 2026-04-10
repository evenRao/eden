from dataclasses import dataclass

import numpy as np

from app.utils.categories import category_fit_score
from app.utils.text import information_density, lexical_tokens


AMBIGUOUS_TERMS = {
    "something",
    "anything",
    "stuff",
    "maybe",
    "possibly",
    "kind",
    "various",
    "somehow",
    "etc",
}
ACTION_TERMS = {
    "write",
    "return",
    "generate",
    "analyze",
    "summarize",
    "explain",
    "classify",
    "extract",
    "compare",
}
CONSTRAINT_TERMS = {
    "exactly",
    "must",
    "format",
    "json",
    "table",
    "include",
    "limit",
    "steps",
    "schema",
}


@dataclass
class ScoreResult:
    overall_score: float
    clarity: float
    specificity: float
    usefulness: float
    inverse_ambiguity: float
    diversity_contribution: float
    category_fit: float
    semantic_novelty: float
    lexical_complexity: float
    breakdown: dict
    explanations: list[str]


class PromptScorer:
    """Transparent heuristic scorer for prompt quality."""

    def __init__(self, similarity_matrix: np.ndarray):
        self.similarity_matrix = similarity_matrix

    def _clarity(self, prompt: str) -> float:
        tokens = lexical_tokens(prompt)
        count = len(tokens)
        action_bonus = 0.15 if set(tokens) & ACTION_TERMS else 0.0
        length_score = 1.0 - min(abs(count - 24) / 32, 1.0)
        punctuation_bonus = 0.1 if ":" in prompt or "." in prompt else 0.0
        return max(0.0, min(1.0, 0.3 + 0.45 * length_score + action_bonus + punctuation_bonus))

    def _specificity(self, prompt: str, expected_behavior: str) -> float:
        tokens = set(lexical_tokens(prompt))
        constraint_bonus = min(0.35, 0.08 * len(tokens & CONSTRAINT_TERMS))
        detail_bonus = min(0.25, len(lexical_tokens(expected_behavior)) / 40)
        numeric_bonus = 0.1 if any(char.isdigit() for char in prompt) else 0.0
        return max(0.0, min(1.0, 0.3 + constraint_bonus + detail_bonus + numeric_bonus))

    def _usefulness(self, prompt: str, expected_behavior: str) -> float:
        density = information_density(prompt)
        behavior_density = information_density(expected_behavior)
        return max(0.0, min(1.0, 0.2 + 0.45 * density + 0.35 * behavior_density))

    def _inverse_ambiguity(self, prompt: str) -> float:
        tokens = lexical_tokens(prompt)
        if not tokens:
            return 0.0
        ambiguous_ratio = len([token for token in tokens if token in AMBIGUOUS_TERMS]) / len(tokens)
        pronoun_penalty = 0.08 if prompt.lower().count(" this ") + prompt.lower().count(" it ") > 1 else 0.0
        return max(0.0, min(1.0, 0.95 - ambiguous_ratio * 2.5 - pronoun_penalty))

    def _diversity_contribution(self, index: int) -> float:
        if self.similarity_matrix.shape[0] <= 1:
            return 1.0
        similarities = np.delete(self.similarity_matrix[index], index)
        top_neighbors = np.sort(similarities)[-3:]
        return float(max(0.0, min(1.0, 1.0 - np.mean(top_neighbors))))

    def _semantic_novelty(self, index: int) -> float:
        if self.similarity_matrix.shape[0] <= 1:
            return 1.0
        similarities = np.delete(self.similarity_matrix[index], index)
        return float(max(0.0, min(1.0, 1.0 - float(np.max(similarities)))))

    def _lexical_complexity(self, prompt: str) -> float:
        tokens = lexical_tokens(prompt)
        if not tokens:
            return 0.0
        avg_length = sum(len(token) for token in tokens) / len(tokens)
        diversity = len(set(tokens)) / len(tokens)
        return max(0.0, min(1.0, 0.35 * diversity + 0.08 * avg_length))

    def score_prompt(
        self,
        index: int,
        prompt: str,
        category: str,
        expected_behavior: str,
    ) -> ScoreResult:
        clarity = self._clarity(prompt)
        specificity = self._specificity(prompt, expected_behavior)
        usefulness = self._usefulness(prompt, expected_behavior)
        inverse_ambiguity = self._inverse_ambiguity(prompt)
        diversity_contribution = self._diversity_contribution(index)
        category_fit = category_fit_score(category, f"{prompt} {expected_behavior}")
        semantic_novelty = self._semantic_novelty(index)
        lexical_complexity = self._lexical_complexity(prompt)

        overall_score = (
            0.20 * clarity
            + 0.15 * specificity
            + 0.15 * usefulness
            + 0.15 * inverse_ambiguity
            + 0.15 * diversity_contribution
            + 0.10 * category_fit
            + 0.10 * semantic_novelty
        )

        explanations: list[str] = []
        if clarity < 0.6:
            explanations.append("Clarity is weak because the request lacks a crisp action or well-sized scope.")
        if specificity < 0.6:
            explanations.append("Specificity is limited; add constraints, formats, or evaluation criteria.")
        if inverse_ambiguity < 0.6:
            explanations.append("Ambiguous wording may cause inconsistent model behavior.")
        if diversity_contribution < 0.55:
            explanations.append("This prompt overlaps heavily with nearby prompts and adds limited dataset diversity.")
        if category_fit > 0.8:
            explanations.append("The prompt strongly matches its assigned category.")
        if semantic_novelty > 0.75:
            explanations.append("The prompt is semantically novel relative to the current dataset.")
        if not explanations:
            explanations.append("This prompt is balanced and should be a useful evaluation candidate.")

        breakdown = {
            "clarity": round(clarity, 4),
            "specificity": round(specificity, 4),
            "usefulness": round(usefulness, 4),
            "inverse_ambiguity": round(inverse_ambiguity, 4),
            "diversity_contribution": round(diversity_contribution, 4),
            "category_fit": round(category_fit, 4),
            "semantic_novelty": round(semantic_novelty, 4),
            "lexical_complexity": round(lexical_complexity, 4),
        }
        return ScoreResult(
            overall_score=round(overall_score, 4),
            clarity=round(clarity, 4),
            specificity=round(specificity, 4),
            usefulness=round(usefulness, 4),
            inverse_ambiguity=round(inverse_ambiguity, 4),
            diversity_contribution=round(diversity_contribution, 4),
            category_fit=round(category_fit, 4),
            semantic_novelty=round(semantic_novelty, 4),
            lexical_complexity=round(lexical_complexity, 4),
            breakdown=breakdown,
            explanations=explanations,
        )

