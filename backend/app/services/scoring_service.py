import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.prompt import PromptItem
from app.models.score import QualityScore
from app.scoring.quality import PromptScorer
from app.utils.artifacts import export_json_artifact
from app.utils.similarity import SemanticSimilarityEngine


class DatasetScoringService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.similarity = SemanticSimilarityEngine(self.settings.similarity_model)

    def score(self, dataset_id: str) -> tuple[Dataset, list[QualityScore], dict, list[str]]:
        dataset = self.db.get(Dataset, dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} was not found.")

        items = (
            self.db.query(PromptItem)
            .filter(PromptItem.dataset_id == dataset_id, PromptItem.is_active.is_(True))
            .order_by(PromptItem.created_at.asc())
            .all()
        )
        if not items:
            raise ValueError("No active prompt items were found for scoring.")

        texts = [item.normalized_prompt or item.prompt for item in items]
        similarity_matrix = self.similarity.similarity_matrix(texts)
        scorer = PromptScorer(similarity_matrix)

        created_scores: list[QualityScore] = []
        for index, item in enumerate(items):
            score = scorer.score_prompt(
                index=index,
                prompt=item.prompt,
                category=item.category,
                expected_behavior=item.expected_behavior,
            )
            score_row = QualityScore(
                prompt_item_id=item.id,
                overall_score=score.overall_score,
                clarity=score.clarity,
                specificity=score.specificity,
                usefulness=score.usefulness,
                inverse_ambiguity=score.inverse_ambiguity,
                diversity_contribution=score.diversity_contribution,
                category_fit=score.category_fit,
                semantic_novelty=score.semantic_novelty,
                lexical_complexity=score.lexical_complexity,
                breakdown=score.breakdown,
                explanations=score.explanations,
                scoring_version=self.settings.scoring_version,
            )
            self.db.add(score_row)
            created_scores.append(score_row)

        dataset.status = "scored"
        self.db.commit()
        for score in created_scores:
            self.db.refresh(score)

        frame = pd.DataFrame(
            [
                {
                    "prompt_item_id": score.prompt_item_id,
                    "overall_score": score.overall_score,
                    "category": item.category,
                    "difficulty": item.difficulty,
                    "clarity": score.clarity,
                    "specificity": score.specificity,
                    "semantic_novelty": score.semantic_novelty,
                }
                for item, score in zip(items, created_scores, strict=True)
            ]
        )
        summary = {
            "average_quality_score": round(float(frame["overall_score"].mean()), 4),
            "median_quality_score": round(float(frame["overall_score"].median()), 4),
            "min_quality_score": round(float(frame["overall_score"].min()), 4),
            "max_quality_score": round(float(frame["overall_score"].max()), 4),
            "category_averages": frame.groupby("category")["overall_score"]
            .mean()
            .round(4)
            .to_dict(),
            "difficulty_averages": frame.groupby("difficulty")["overall_score"]
            .mean()
            .round(4)
            .to_dict(),
        }
        dataset.dataset_metadata = {
            **dataset.dataset_metadata,
            "scoring": summary,
        }
        self.db.commit()

        artifacts: list[str] = []
        if self.settings.export_artifacts:
            artifact_path = self.settings.data_dir / "scored" / f"{dataset.id}.json"
            artifacts.append(
                export_json_artifact(
                    artifact_path,
                    {
                        "dataset_id": dataset.id,
                        "status": dataset.status,
                        "summary": summary,
                        "scores": [
                            {
                                "prompt_item_id": score.prompt_item_id,
                                "overall_score": score.overall_score,
                                "breakdown": score.breakdown,
                                "explanations": score.explanations,
                            }
                            for score in created_scores
                        ],
                    },
                )
            )

        return dataset, created_scores, summary, artifacts

