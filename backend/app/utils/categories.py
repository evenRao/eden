from collections import Counter

from app.schemas.common import PromptCategory
from app.utils.text import lexical_tokens


CATEGORY_KEYWORDS: dict[str, set[str]] = {
    PromptCategory.coding.value: {
        "code",
        "python",
        "debug",
        "function",
        "algorithm",
        "refactor",
        "test",
        "sql",
        "api",
    },
    PromptCategory.reasoning.value: {
        "reason",
        "logic",
        "infer",
        "step",
        "tradeoff",
        "compare",
        "analyze",
        "deduce",
    },
    PromptCategory.summarization.value: {
        "summarize",
        "summary",
        "brief",
        "article",
        "transcript",
        "report",
        "condense",
    },
    PromptCategory.explanation.value: {
        "explain",
        "teach",
        "describe",
        "concept",
        "beginner",
        "intuition",
        "walkthrough",
    },
    PromptCategory.factual_qa.value: {
        "what",
        "when",
        "where",
        "who",
        "fact",
        "evidence",
        "cite",
        "definition",
    },
    PromptCategory.instruction_following.value: {
        "follow",
        "instructions",
        "exactly",
        "constraints",
        "format",
        "steps",
        "must",
        "return",
    },
    PromptCategory.safety_sensitive_refusal.value: {
        "refuse",
        "unsafe",
        "harmful",
        "policy",
        "security",
        "exploit",
        "weapon",
        "malware",
    },
    PromptCategory.structured_output.value: {
        "json",
        "schema",
        "yaml",
        "table",
        "fields",
        "array",
        "object",
        "structured",
    },
}


def guess_category(text: str, default: str = PromptCategory.reasoning.value) -> str:
    """Assign a category from keyword overlap."""

    counts = Counter()
    tokens = set(lexical_tokens(text))
    for category, keywords in CATEGORY_KEYWORDS.items():
        counts[category] = len(tokens & keywords)
    best_category, best_score = counts.most_common(1)[0]
    return best_category if best_score > 0 else default


def category_fit_score(category: str, text: str) -> float:
    tokens = set(lexical_tokens(text))
    keywords = CATEGORY_KEYWORDS.get(category, set())
    if not keywords:
        return 0.5
    overlap = len(tokens & keywords)
    base = overlap / max(4, len(keywords) / 2)
    return max(0.0, min(1.0, 0.4 + base))

