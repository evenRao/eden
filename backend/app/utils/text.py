import re
import string
from collections.abc import Iterable


WHITESPACE_RE = re.compile(r"\s+")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?])")


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_punctuation_spacing(text: str) -> str:
    text = normalize_whitespace(text)
    return SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)


def normalize_text(text: str) -> str:
    return normalize_punctuation_spacing(text)


def lexical_tokens(text: str) -> list[str]:
    translator = str.maketrans("", "", string.punctuation)
    cleaned = text.lower().translate(translator)
    return [token for token in cleaned.split() if token]


def information_density(text: str) -> float:
    tokens = lexical_tokens(text)
    if not tokens:
        return 0.0
    unique_ratio = len(set(tokens)) / len(tokens)
    return min(1.0, 0.5 * unique_ratio + min(len(tokens), 40) / 80)


def join_non_empty(parts: Iterable[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())

