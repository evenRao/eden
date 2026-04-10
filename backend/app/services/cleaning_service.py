from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.prompt import PromptItem
from app.utils.artifacts import export_json_artifact
from app.utils.categories import guess_category
from app.utils.similarity import SemanticSimilarityEngine
from app.utils.text import information_density, normalize_text


class DatasetCleaningService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.similarity = SemanticSimilarityEngine(self.settings.similarity_model)

    def clean(
        self,
        dataset_id: str,
        semantic_threshold: float,
        remove_low_information: bool = True,
    ) -> dict:
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
            raise ValueError("No active prompt items were found for the dataset.")

        exact_seen: dict[str, PromptItem] = {}
        candidates: list[PromptItem] = []
        removed_exact = 0
        removed_low_info = 0

        for item in items:
            item.normalized_prompt = normalize_text(item.prompt)
            if not item.category:
                item.category = guess_category(item.prompt)

            low_info = information_density(item.prompt) < 0.24 or len(item.prompt.split()) < 6
            if remove_low_information and low_info:
                item.is_active = False
                item.lifecycle_stage = "removed_low_information"
                item.attributes = {**item.attributes, "cleaning_reason": "low_information"}
                removed_low_info += 1
                continue

            normalized_key = item.normalized_prompt.lower()
            if normalized_key in exact_seen:
                item.is_active = False
                item.lifecycle_stage = "removed_exact_duplicate"
                item.attributes = {
                    **item.attributes,
                    "duplicate_of": exact_seen[normalized_key].id,
                    "duplicate_type": "exact",
                }
                removed_exact += 1
                continue

            exact_seen[normalized_key] = item
            candidates.append(item)

        removed_semantic = 0
        texts = [item.normalized_prompt or item.prompt for item in candidates]
        matrix = self.similarity.similarity_matrix(texts)
        discarded_indices: set[int] = set()

        for i in range(len(candidates)):
            if i in discarded_indices:
                continue
            for j in range(i + 1, len(candidates)):
                if j in discarded_indices or matrix[i, j] < semantic_threshold:
                    continue

                keep_i_score = information_density(candidates[i].prompt) + information_density(
                    candidates[i].expected_behavior
                )
                keep_j_score = information_density(candidates[j].prompt) + information_density(
                    candidates[j].expected_behavior
                )

                keep_index, discard_index = (i, j) if keep_i_score >= keep_j_score else (j, i)
                discarded_indices.add(discard_index)
                duplicate_item = candidates[discard_index]
                duplicate_item.is_active = False
                duplicate_item.lifecycle_stage = "removed_near_duplicate"
                duplicate_item.attributes = {
                    **duplicate_item.attributes,
                    "duplicate_of": candidates[keep_index].id,
                    "duplicate_type": "semantic",
                    "semantic_similarity": round(float(matrix[i, j]), 4),
                }
                removed_semantic += 1

        kept_items: list[PromptItem] = []
        for index, item in enumerate(candidates):
            if index in discarded_indices:
                continue
            item.lifecycle_stage = "cleaned"
            item.category = item.category or guess_category(item.prompt)
            kept_items.append(item)

        dataset.status = "cleaned"
        dataset.dataset_metadata = {
            **dataset.dataset_metadata,
            "cleaning": {
                "removed_exact_duplicates": removed_exact,
                "removed_semantic_duplicates": removed_semantic,
                "removed_low_information": removed_low_info,
                "semantic_backend": self.similarity.backend,
                "semantic_threshold": semantic_threshold,
            },
        }
        self.db.commit()

        artifacts: list[str] = []
        if self.settings.export_artifacts:
            artifact_path = self.settings.data_dir / "cleaned" / f"{dataset.id}.json"
            artifacts.append(
                export_json_artifact(
                    artifact_path,
                    {
                        "dataset_id": dataset.id,
                        "status": dataset.status,
                        "summary": dataset.dataset_metadata["cleaning"],
                        "items": [
                            {
                                "id": item.id,
                                "prompt": item.prompt,
                                "normalized_prompt": item.normalized_prompt,
                                "category": item.category,
                                "difficulty": item.difficulty,
                                "expected_behavior": item.expected_behavior,
                                "tags": item.tags,
                                "version": item.version,
                            }
                            for item in kept_items
                        ],
                    },
                )
            )

        return {
            "dataset": dataset,
            "items": kept_items,
            "artifacts": artifacts,
            "summary": dataset.dataset_metadata["cleaning"],
        }

