from app.generators.dataset_generator import TemplateDatasetGenerator


def test_template_generator_produces_requested_count_and_categories():
    generator = TemplateDatasetGenerator(seed=11)
    items = generator.generate(
        num_items=8,
        categories=["coding", "structured_output"],
        difficulties=["medium"],
    )

    assert len(items) == 8
    assert {item.category for item in items} <= {"coding", "structured_output"}
    assert all(item.expected_behavior for item in items)
    assert all(item.id for item in items)

