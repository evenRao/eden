from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal, init_db
from app.monitoring.aggregator import MetricsAggregator
from app.schemas.dataset import CleanDatasetRequest, GenerateDatasetRequest
from app.schemas.evaluation import EvaluateDatasetRequest, ModelConfig
from app.schemas.improvement import ImproveDatasetRequest
from app.services.cleaning_service import DatasetCleaningService
from app.services.evaluation_service import EvaluationService
from app.services.generation_service import DatasetGenerationService
from app.services.improvement_service import ImprovementService
from app.services.scoring_service import DatasetScoringService


def create_charts(metrics: dict, dataset_id: str) -> list[str]:
    chart_dir = PROJECT_ROOT / "evaluation" / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    category_distribution = metrics["dataset_metrics"].get("category_distribution", {})
    if category_distribution:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(category_distribution.keys(), category_distribution.values(), color="#2E6F95")
        ax.set_title("Prompt Category Distribution")
        ax.set_ylabel("Prompt Count")
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        path = chart_dir / f"{dataset_id}_category_distribution.png"
        fig.savefig(path)
        plt.close(fig)
        paths.append(str(path))

    model_metrics = metrics.get("model_metrics", [])
    if model_metrics:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(
            [entry["model_name"] for entry in model_metrics],
            [entry["average_heuristic_quality"] for entry in model_metrics],
            color="#A6513D",
        )
        ax.set_title("Average Heuristic Quality by Model")
        ax.set_ylim(0, 1)
        fig.tight_layout()
        path = chart_dir / f"{dataset_id}_model_quality.png"
        fig.savefig(path)
        plt.close(fig)
        paths.append(str(path))

    return paths


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        dataset, _items, generation_artifacts = DatasetGenerationService(db).generate(
            GenerateDatasetRequest(
                dataset_name="eden-demo-dataset",
                description="Sample prompt dataset for the E.D.E.N. demo pipeline.",
                num_items=16,
                seed=7,
                llm_assisted=False,
            )
        )

        clean_result = DatasetCleaningService(db).clean(
            dataset_id=dataset.id,
            semantic_threshold=0.9,
            remove_low_information=True,
        )
        _dataset, _scores, scoring_summary, scoring_artifacts = DatasetScoringService(db).score(
            dataset.id
        )
        evaluations = EvaluationService(db).evaluate(
            EvaluateDatasetRequest(
                dataset_id=dataset.id,
                repeats=2,
                models=[
                    ModelConfig(backend="mock", model_name="eden-mock-001"),
                    ModelConfig(backend="mock", model_name="eden-mock-002", temperature=0.35),
                ],
            )
        )
        improvements = ImprovementService(db).improve(
            ImproveDatasetRequest(dataset_id=dataset.id, quality_threshold=0.68, max_candidates=6)
        )
        metrics = MetricsAggregator(db).collect(dataset_id=dataset.id, persist_snapshot=True)
        chart_paths = create_charts(metrics, dataset.id)

        summary_path = PROJECT_ROOT / "evaluation" / "demo_summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "dataset_id": dataset.id,
                    "generation_artifacts": generation_artifacts,
                    "cleaning_summary": clean_result["summary"],
                    "scoring_summary": scoring_summary,
                    "evaluation_run_ids": [run.id for run in evaluations],
                    "improvement_count": len(improvements),
                    "chart_paths": chart_paths,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        print(json.dumps({"dataset_id": dataset.id, "charts": chart_paths}, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()

