from app.evaluators.base import BaseEvaluator
from app.evaluators.huggingface import HuggingFaceEvaluator
from app.evaluators.mock import MockEvaluator
from app.evaluators.ollama import OllamaEvaluator
from app.evaluators.openai_evaluator import OpenAIEvaluator
from app.schemas.common import ModelBackend
from app.schemas.evaluation import ModelConfig


def build_evaluator(config: ModelConfig) -> BaseEvaluator:
    if config.backend == ModelBackend.mock:
        return MockEvaluator(config.model_name, config.temperature, config.max_tokens)
    if config.backend == ModelBackend.ollama:
        return OllamaEvaluator(config.model_name, config.temperature, config.max_tokens)
    if config.backend == ModelBackend.openai:
        return OpenAIEvaluator(config.model_name, config.temperature, config.max_tokens)
    if config.backend == ModelBackend.huggingface:
        return HuggingFaceEvaluator(config.model_name, config.temperature, config.max_tokens)
    raise ValueError(f"Unsupported model backend: {config.backend}")

