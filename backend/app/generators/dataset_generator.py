import random
from dataclasses import asdict, dataclass

from app.generators.template_library import SLOT_VALUES, TEMPLATES, PromptTemplate
from app.schemas.common import DifficultyLevel, PromptCategory
from app.utils.ids import generate_uuid
from app.utils.text import join_non_empty


@dataclass
class GeneratedPromptRecord:
    id: str
    prompt: str
    category: str
    difficulty: str
    expected_behavior: str
    source: str
    tags: list[str]
    attributes: dict
    version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


class TemplateDatasetGenerator:
    """Generate prompt items from seeded templates with deterministic randomness."""

    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)

    def _fill_template(self, template: PromptTemplate) -> str:
        values = {slot: self.random.choice(options) for slot, options in SLOT_VALUES.items()}
        prompt = template.prompt_template.format(**values)
        if template.category == PromptCategory.reasoning.value and self.random.random() > 0.5:
            prompt = join_non_empty([prompt, "Highlight assumptions and failure modes."])
        if template.category == PromptCategory.structured_output.value and self.random.random() > 0.4:
            prompt = join_non_empty([prompt, "Use stable field names and no extra commentary."])
        return prompt

    def generate(
        self,
        num_items: int,
        categories: list[str] | None = None,
        difficulties: list[str] | None = None,
        llm_assisted: bool = False,
    ) -> list[GeneratedPromptRecord]:
        allowed_categories = set(categories or [category.value for category in PromptCategory])
        allowed_difficulties = set(
            difficulties or [difficulty.value for difficulty in DifficultyLevel]
        )
        eligible_templates = [
            template
            for template in TEMPLATES
            if template.category in allowed_categories and template.difficulty in allowed_difficulties
        ]
        if not eligible_templates:
            raise ValueError("No templates matched the requested categories and difficulties.")

        records: list[GeneratedPromptRecord] = []
        for index in range(num_items):
            template = eligible_templates[index % len(eligible_templates)]
            prompt = self._fill_template(template)
            if llm_assisted:
                prompt = join_non_empty(
                    [prompt, "Ensure the prompt can separate strong and weak model behaviors."]
                )
            records.append(
                GeneratedPromptRecord(
                    id=generate_uuid(),
                    prompt=prompt,
                    category=template.category,
                    difficulty=template.difficulty,
                    expected_behavior=template.expected_behavior,
                    source="llm" if llm_assisted else "template",
                    tags=list(template.tags),
                    attributes={"template_index": index % len(eligible_templates)},
                )
            )
        self.random.shuffle(records)
        return records

