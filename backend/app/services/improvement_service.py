from collections import defaultdict

from sqlalchemy.orm import Session

from app.improvement.rewriter import PromptImprover
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationRun, ModelOutput
from app.models.improvement import ImprovementRecord
from app.models.prompt import PromptItem
from app.models.score import QualityScore
from app.scoring.quality import PromptScorer
from app.schemas.improvement import ImproveDatasetRequest
from app.utils.similarity import SemanticSimilarityEngine
from app.utils.text import normalize_text


class ImprovementService:
    def __init__(self, db: Session):
        self.db = db
        self.similarity = SemanticSimilarityEngine("sentence-transformers/all-MiniLM-L6-v2")
        self.improver = PromptImprover()

    def improve(self, request: ImproveDatasetRequest) -> list[ImprovementRecord]:
        dataset = self.db.get(Dataset, request.dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {request.dataset_id} was not found.")

        active_items = (
            self.db.query(PromptItem)
            .filter(PromptItem.dataset_id == request.dataset_id, PromptItem.is_active.is_(True))
            .order_by(PromptItem.created_at.asc())
            .all()
        )
        latest_scores = self._latest_scores_for_dataset(request.dataset_id)
        discriminative_power = self._discriminative_power_by_prompt(request.dataset_id)

        candidates = [
            item
            for item in active_items
            if item.id in latest_scores
            and (
                latest_scores[item.id].overall_score < request.quality_threshold
                or latest_scores[item.id].diversity_contribution < 0.5
                or latest_scores[item.id].category_fit < 0.58
                or discriminative_power.get(item.id, 1.0) < 0.05
            )
        ][: request.max_candidates]

        improvement_records: list[ImprovementRecord] = []
        for item in candidates:
            before_score = latest_scores[item.id]
            low_discriminative_power = discriminative_power.get(item.id, 1.0) < 0.05
            rewrite = self.improver.rewrite(
                item=item,
                score=before_score,
                low_discriminative_power=low_discriminative_power,
            )
            candidate_score = self._score_candidate(
                active_items=active_items,
                original_item=item,
                new_prompt=rewrite["prompt"],
                category=item.category,
                expected_behavior=rewrite["expected_behavior"],
            )
            accepted = candidate_score.overall_score > before_score.overall_score + 0.02

            improved_prompt_item_id: str | None = None
            if accepted:
                item.is_active = False
                item.lifecycle_stage = "superseded"
                improved_item = PromptItem(
                    dataset_id=item.dataset_id,
                    parent_prompt_item_id=item.id,
                    prompt=rewrite["prompt"],
                    normalized_prompt=normalize_text(rewrite["prompt"]),
                    category=item.category,
                    difficulty=rewrite["difficulty"],
                    expected_behavior=rewrite["expected_behavior"],
                    source="improved",
                    tags=list(item.tags),
                    attributes={
                        **item.attributes,
                        "improved_from": item.id,
                        "improvement_action": rewrite["action"],
                    },
                    version=item.version + 1,
                    is_active=True,
                    lifecycle_stage="improved",
                )
                self.db.add(improved_item)
                self.db.flush()
                improved_prompt_item_id = improved_item.id

                improved_score = QualityScore(
                    prompt_item_id=improved_item.id,
                    overall_score=candidate_score.overall_score,
                    clarity=candidate_score.clarity,
                    specificity=candidate_score.specificity,
                    usefulness=candidate_score.usefulness,
                    inverse_ambiguity=candidate_score.inverse_ambiguity,
                    diversity_contribution=candidate_score.diversity_contribution,
                    category_fit=candidate_score.category_fit,
                    semantic_novelty=candidate_score.semantic_novelty,
                    lexical_complexity=candidate_score.lexical_complexity,
                    breakdown=candidate_score.breakdown,
                    explanations=candidate_score.explanations,
                    scoring_version="v1-improvement",
                )
                self.db.add(improved_score)

            record = ImprovementRecord(
                dataset_id=dataset.id,
                original_prompt_item_id=item.id,
                improved_prompt_item_id=improved_prompt_item_id,
                action=rewrite["action"],
                reason=rewrite["reason"],
                accepted=accepted,
                score_before=before_score.overall_score,
                score_after=candidate_score.overall_score,
                analysis={
                    "weaknesses": rewrite["weaknesses"],
                    "before_breakdown": before_score.breakdown,
                    "after_breakdown": candidate_score.breakdown,
                    "low_discriminative_power": low_discriminative_power,
                },
            )
            self.db.add(record)
            improvement_records.append(record)

        if improvement_records:
            dataset.status = "improved"
        self.db.commit()
        for record in improvement_records:
            self.db.refresh(record)
        return improvement_records

    def _latest_scores_for_dataset(self, dataset_id: str) -> dict[str, QualityScore]:
        items = (
            self.db.query(PromptItem)
            .filter(PromptItem.dataset_id == dataset_id)
            .order_by(PromptItem.created_at.asc())
            .all()
        )
        prompt_ids = [item.id for item in items]
        score_rows = (
            self.db.query(QualityScore)
            .filter(QualityScore.prompt_item_id.in_(prompt_ids))
            .order_by(QualityScore.created_at.desc())
            .all()
        )
        latest: dict[str, QualityScore] = {}
        for score in score_rows:
            latest.setdefault(score.prompt_item_id, score)
        return latest

    def _discriminative_power_by_prompt(self, dataset_id: str) -> dict[str, float]:
        outputs = (
            self.db.query(ModelOutput, EvaluationRun.model_name)
            .join(EvaluationRun, ModelOutput.evaluation_run_id == EvaluationRun.id)
            .join(PromptItem, ModelOutput.prompt_item_id == PromptItem.id)
            .filter(PromptItem.dataset_id == dataset_id)
            .all()
        )
        grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for output, model_name in outputs:
            grouped[output.prompt_item_id][model_name].append(output.heuristic_quality)

        spread: dict[str, float] = {}
        for prompt_id, by_model in grouped.items():
            model_means = [sum(values) / len(values) for values in by_model.values() if values]
            spread[prompt_id] = max(model_means) - min(model_means) if len(model_means) >= 2 else 1.0
        return spread

    def _score_candidate(
        self,
        active_items: list[PromptItem],
        original_item: PromptItem,
        new_prompt: str,
        category: str,
        expected_behavior: str,
    ):
        texts = []
        target_index = 0
        for item in active_items:
            if item.id == original_item.id:
                target_index = len(texts)
                texts.append(new_prompt)
            elif item.is_active:
                texts.append(item.normalized_prompt or item.prompt)

        similarity_matrix = self.similarity.similarity_matrix(texts)
        scorer = PromptScorer(similarity_matrix)
        return scorer.score_prompt(
            index=target_index,
            prompt=new_prompt,
            category=category,
            expected_behavior=expected_behavior,
        )
