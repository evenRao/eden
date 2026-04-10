from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.generators.dataset_generator import TemplateDatasetGenerator
from app.models.dataset import Dataset
from app.models.prompt import PromptItem
from app.schemas.dataset import GenerateDatasetRequest
from app.utils.artifacts import export_json_artifact
from app.utils.text import normalize_text


class DatasetGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def generate(self, request: GenerateDatasetRequest) -> tuple[Dataset, list[PromptItem], list[str]]:
        generator = TemplateDatasetGenerator(seed=request.seed)
        records = generator.generate(
            num_items=request.num_items,
            categories=[category.value for category in request.categories] or None,
            difficulties=[difficulty.value for difficulty in request.difficulties] or None,
            llm_assisted=request.llm_assisted,
        )

        dataset = Dataset(
            name=request.dataset_name,
            description=request.description,
            source="llm" if request.llm_assisted else "template",
            status="generated",
            tags=request.tags,
            dataset_metadata={
                "seed": request.seed,
                "num_items_requested": request.num_items,
                "llm_assisted": request.llm_assisted,
            },
        )
        self.db.add(dataset)
        self.db.flush()

        prompt_items: list[PromptItem] = []
        for record in records:
            prompt_item = PromptItem(
                id=record.id,
                dataset_id=dataset.id,
                prompt=record.prompt,
                normalized_prompt=normalize_text(record.prompt),
                category=record.category,
                difficulty=record.difficulty,
                expected_behavior=record.expected_behavior,
                source=record.source,
                tags=record.tags,
                attributes=record.attributes,
                version=record.version,
                lifecycle_stage="generated",
            )
            prompt_items.append(prompt_item)
            self.db.add(prompt_item)

        self.db.commit()
        self.db.refresh(dataset)
        for item in prompt_items:
            self.db.refresh(item)

        artifacts: list[str] = []
        if self.settings.export_artifacts:
            artifact_path = (
                self.settings.data_dir / "generated" / f"{dataset.id}.json"
            )
            artifacts.append(
                export_json_artifact(
                    artifact_path,
                    {
                        "dataset": {
                            "id": dataset.id,
                            "name": dataset.name,
                            "status": dataset.status,
                            "source": dataset.source,
                        },
                        "items": [
                            {
                                "id": item.id,
                                "prompt": item.prompt,
                                "category": item.category,
                                "difficulty": item.difficulty,
                                "expected_behavior": item.expected_behavior,
                                "source": item.source,
                                "tags": item.tags,
                                "created_at": item.created_at,
                                "version": item.version,
                            }
                            for item in prompt_items
                        ],
                    },
                )
            )

        return dataset, prompt_items, artifacts

