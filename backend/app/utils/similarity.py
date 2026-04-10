import logging
from functools import cached_property

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


logger = logging.getLogger(__name__)


class SemanticSimilarityEngine:
    """Compute semantic similarity with sentence-transformers and a TF-IDF fallback."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.backend = "uninitialized"
        self._encoder_attempted = False

    @cached_property
    def _tfidf(self) -> TfidfVectorizer:
        return TfidfVectorizer(ngram_range=(1, 2), min_df=1)

    def _load_sentence_encoder(self):  # type: ignore[no-untyped-def]
        if self._encoder_attempted:
            return None
        self._encoder_attempted = True
        try:
            from sentence_transformers import SentenceTransformer

            encoder = SentenceTransformer(self.model_name)
            self.backend = "sentence_transformer"
            return encoder
        except Exception as exc:  # pragma: no cover - fallback depends on environment
            logger.warning(
                "Falling back to TF-IDF similarity because the sentence model failed: %s",
                exc,
            )
            self.backend = "tfidf"
            return None

    @cached_property
    def _sentence_encoder(self):  # type: ignore[no-untyped-def]
        return self._load_sentence_encoder()

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            self.backend = "tfidf"
            return np.zeros((0, 0))

        if self._sentence_encoder is not None:
            embeddings = self._sentence_encoder.encode(texts, normalize_embeddings=True)
            return np.array(embeddings)

        matrix = self._tfidf.fit_transform(texts)
        self.backend = "tfidf"
        return matrix.toarray()

    def similarity_matrix(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0))
        encoded = self.encode(texts)
        if encoded.size == 0:
            return np.zeros((len(texts), len(texts)))
        return cosine_similarity(encoded)

    def pairwise_similarity_mean(self, texts: list[str]) -> float:
        matrix = self.similarity_matrix(texts)
        if len(texts) < 2:
            return 1.0 if texts else 0.0
        upper = matrix[np.triu_indices(len(texts), k=1)]
        return float(np.mean(upper)) if upper.size else 1.0

