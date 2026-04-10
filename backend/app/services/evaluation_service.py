from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session

from app.evaluators.factory import build_evaluator
from app.evaluators.heuristics import evaluate_response
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationRun, ModelOutput
from app.models.prompt import PromptItem
from app.schemas.evaluation import EvaluateDatasetRequest, ModelConfig
from app.utils.similarity import SemanticSimilarityEngine
from app.utils.time import utcnow


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.similarity = SemanticSimilarityEngine("sentence-transformers/all-MiniLM-L6-v2")

    def evaluate(self, request: EvaluateDatasetRequest) -> list[EvaluationRun]:
        dataset = self.db.get(Dataset, request.dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {request.dataset_id} was not found.")

        items = (
            self.db.query(PromptItem)
            .filter(PromptItem.dataset_id == request.dataset_id, PromptItem.is_active.is_(True))
            .order_by(PromptItem.created_at.asc())
            .all()
        )
        if not items:
            raise ValueError("No active prompt items were found for evaluation.")

        model_configs = request.models or [ModelConfig()]
        runs: list[EvaluationRun] = []
        for config in model_configs:
            evaluator = build_evaluator(config)
            run = EvaluationRun(
                dataset_id=dataset.id,
                run_name=request.run_name or f"{dataset.name}-{config.model_name}",
                backend=config.backend.value,
                model_name=config.model_name,
                repeats=request.repeats,
                status="running",
                notes=request.notes,
                aggregate_metrics={},
            )
            self.db.add(run)
            self.db.flush()

            outputs_by_prompt: dict[str, list[ModelOutput]] = defaultdict(list)

            for item in items:
                for attempt_index in range(request.repeats):
                    result = evaluator.generate(
                        prompt=item.prompt,
                        category=item.category,
                        expected_behavior=item.expected_behavior,
                        attempt_index=attempt_index,
                    )
                    heuristics = evaluate_response(
                        prompt=item.prompt,
                        response_text=result.text,
                        category=item.category,
                        expected_behavior=item.expected_behavior,
                    )
                    output = ModelOutput(
                        evaluation_run_id=run.id,
                        prompt_item_id=item.id,
                        attempt_index=attempt_index,
                        response_text=result.text,
                        latency_ms=result.latency_ms,
                        response_length=len(result.text.split()),
                        failure=result.failure,
                        structured_output_valid=heuristics.structured_output_valid,
                        response_completeness=heuristics.response_completeness,
                        length_appropriateness=heuristics.length_appropriateness,
                        refusal_correctness=heuristics.refusal_correctness,
                        expected_behavior_overlap=heuristics.expected_behavior_overlap,
                        heuristic_quality=heuristics.heuristic_quality,
                        evaluator_notes=heuristics.notes,
                        raw_metadata=result.metadata,
                        error_message=result.error_message,
                    )
                    outputs_by_prompt[item.id].append(output)
                    self.db.add(output)

            for prompt_outputs in outputs_by_prompt.values():
                consistency = self.similarity.pairwise_similarity_mean(
                    [output.response_text for output in prompt_outputs if output.response_text]
                )
                for output in prompt_outputs:
                    output.consistency_score = round(consistency, 4)

            self.db.flush()
            run.aggregate_metrics = self._aggregate_metrics(items, outputs_by_prompt)
            run.status = "completed"
            run.completed_at = utcnow()
            dataset.status = "evaluated"
            runs.append(run)

        self.db.commit()
        for run in runs:
            self.db.refresh(run)
        return runs

    def _aggregate_metrics(
        self,
        items: list[PromptItem],
        outputs_by_prompt: dict[str, list[ModelOutput]],
    ) -> dict:
        rows = []
        item_lookup = {item.id: item for item in items}
        for prompt_id, outputs in outputs_by_prompt.items():
            item = item_lookup[prompt_id]
            for output in outputs:
                rows.append(
                    {
                        "prompt_item_id": prompt_id,
                        "category": item.category,
                        "latency_ms": output.latency_ms,
                        "response_length": output.response_length,
                        "failure": output.failure,
                        "structured_output_valid": output.structured_output_valid,
                        "heuristic_quality": output.heuristic_quality,
                        "consistency_score": output.consistency_score or 0.0,
                    }
                )

        frame = pd.DataFrame(rows)
        structured_series = frame["structured_output_valid"].dropna().astype(float)
        return {
            "average_latency_ms": round(float(frame["latency_ms"].mean()), 4),
            "average_response_length": round(float(frame["response_length"].mean()), 4),
            "failure_rate": round(float(frame["failure"].mean()), 4),
            "average_heuristic_quality": round(float(frame["heuristic_quality"].mean()), 4),
            "average_consistency": round(float(frame["consistency_score"].mean()), 4),
            "structured_output_valid_rate": round(
                float(structured_series.mean()), 4
            )
            if not structured_series.empty
            else None,
            "category_performance": frame.groupby("category")["heuristic_quality"]
            .mean()
            .round(4)
            .to_dict(),
        }

