from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.evaluation import EvaluationRun, ModelOutput
from app.models.metrics import MetricSnapshot
from app.models.prompt import PromptItem
from app.models.score import QualityScore


class MetricsAggregator:
    """Aggregate dataset and model metrics, and persist time-based snapshots."""

    def __init__(self, db: Session):
        self.db = db

    def collect(self, dataset_id: str | None = None, persist_snapshot: bool = False) -> dict:
        dataset_query = self.db.query(Dataset)
        if dataset_id:
            dataset_query = dataset_query.filter(Dataset.id == dataset_id)
        datasets = dataset_query.order_by(Dataset.created_at.asc()).all()
        if dataset_id and not datasets:
            return {
                "dataset_metrics": {
                    "dataset_count": 0,
                    "total_prompts": 0,
                    "active_prompts": 0,
                    "average_quality_score": None,
                    "category_distribution": {},
                    "difficulty_distribution": {},
                    "duplicate_rate": 0.0,
                    "average_latency_by_model": {},
                    "average_heuristic_quality_by_model": {},
                },
                "model_metrics": [],
                "trend_snapshots": [],
            }

        dataset_ids = [dataset.id for dataset in datasets]
        prompt_query = self.db.query(PromptItem)
        if dataset_id:
            prompt_query = prompt_query.filter(PromptItem.dataset_id.in_(dataset_ids))
        prompts = prompt_query.all()

        score_query = self.db.query(QualityScore).join(
            PromptItem, QualityScore.prompt_item_id == PromptItem.id
        )
        if dataset_id:
            score_query = score_query.filter(PromptItem.dataset_id.in_(dataset_ids))
        score_rows = score_query.order_by(QualityScore.created_at.desc()).all()
        latest_scores: dict[str, QualityScore] = {}
        for score in score_rows:
            latest_scores.setdefault(score.prompt_item_id, score)

        output_query = self.db.query(ModelOutput, EvaluationRun.model_name).join(
            EvaluationRun, ModelOutput.evaluation_run_id == EvaluationRun.id
        )
        if dataset_id:
            output_query = output_query.join(
                PromptItem, ModelOutput.prompt_item_id == PromptItem.id
            ).filter(PromptItem.dataset_id.in_(dataset_ids))
        outputs = output_query.all()

        dataset_metrics = self._dataset_metrics(datasets, prompts, latest_scores, outputs)
        model_metrics = self._model_metrics(prompts, outputs)

        if persist_snapshot:
            snapshot = MetricSnapshot(
                dataset_id=dataset_id,
                snapshot_type="metrics",
                payload={
                    "dataset_metrics": dataset_metrics,
                    "model_metrics": model_metrics,
                },
            )
            self.db.add(snapshot)
            self.db.commit()

        snapshots_query = self.db.query(MetricSnapshot)
        if dataset_id:
            snapshots_query = snapshots_query.filter(MetricSnapshot.dataset_id == dataset_id)
        snapshots = snapshots_query.order_by(MetricSnapshot.created_at.desc()).limit(20).all()

        return {
            "dataset_metrics": dataset_metrics,
            "model_metrics": model_metrics,
            "trend_snapshots": snapshots,
        }

    def _dataset_metrics(
        self,
        datasets: list[Dataset],
        prompts: list[PromptItem],
        latest_scores: dict[str, QualityScore],
        outputs: list[tuple[ModelOutput, str]],
    ) -> dict:
        total_prompts = len(prompts)
        active_prompts = [prompt for prompt in prompts if prompt.is_active]
        duplicate_like = [
            prompt
            for prompt in prompts
            if "duplicate" in prompt.lifecycle_stage or prompt.lifecycle_stage == "superseded"
        ]
        score_values = [latest_scores[prompt.id].overall_score for prompt in active_prompts if prompt.id in latest_scores]

        category_distribution = pd.Series([prompt.category for prompt in active_prompts]).value_counts().to_dict()
        difficulty_distribution = pd.Series([prompt.difficulty for prompt in active_prompts]).value_counts().to_dict()

        output_rows = [
            {
                "latency_ms": output.latency_ms,
                "heuristic_quality": output.heuristic_quality,
                "model_name": model_name,
            }
            for output, model_name in outputs
        ]
        output_frame = pd.DataFrame(output_rows)

        return {
            "dataset_count": len(datasets),
            "total_prompts": total_prompts,
            "active_prompts": len(active_prompts),
            "average_quality_score": round(sum(score_values) / len(score_values), 4)
            if score_values
            else None,
            "category_distribution": category_distribution,
            "difficulty_distribution": difficulty_distribution,
            "duplicate_rate": round(len(duplicate_like) / total_prompts, 4) if total_prompts else 0.0,
            "average_latency_by_model": output_frame.groupby("model_name")["latency_ms"]
            .mean()
            .round(4)
            .to_dict()
            if not output_frame.empty
            else {},
            "average_heuristic_quality_by_model": output_frame.groupby("model_name")[
                "heuristic_quality"
            ]
            .mean()
            .round(4)
            .to_dict()
            if not output_frame.empty
            else {},
        }

    def _model_metrics(
        self,
        prompts: list[PromptItem],
        outputs: list[tuple[ModelOutput, str]],
    ) -> list[dict]:
        if not outputs:
            return []

        prompt_lookup = {prompt.id: prompt for prompt in prompts}
        rows = []
        for output, model_name in outputs:
            prompt = prompt_lookup.get(output.prompt_item_id)
            if prompt is None:
                continue
            rows.append(
                {
                    "model_name": model_name,
                    "category": prompt.category,
                    "latency_ms": output.latency_ms,
                    "failure": output.failure,
                    "consistency_score": output.consistency_score or 0.0,
                    "heuristic_quality": output.heuristic_quality,
                }
            )

        frame = pd.DataFrame(rows)
        metrics: list[dict] = []
        for model_name, group in frame.groupby("model_name"):
            category_scores = group.groupby("category")["heuristic_quality"].mean()
            metrics.append(
                {
                    "model_name": model_name,
                    "average_latency_ms": round(float(group["latency_ms"].mean()), 4),
                    "failure_rate": round(float(group["failure"].mean()), 4),
                    "average_consistency": round(float(group["consistency_score"].mean()), 4),
                    "average_heuristic_quality": round(
                        float(group["heuristic_quality"].mean()), 4
                    ),
                    "best_category": str(category_scores.idxmax()),
                    "worst_category": str(category_scores.idxmin()),
                }
            )
        return metrics
