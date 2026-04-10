from app.models.dataset import Dataset
from app.models.prompt import PromptItem
from app.models.score import QualityScore
from app.services.cleaning_service import DatasetCleaningService
from app.services.improvement_service import ImprovementService
from app.services.scoring_service import DatasetScoringService


def test_cleaning_service_removes_exact_duplicates(db_session):
    dataset = Dataset(name="cleaning-test", source="manual", status="generated")
    db_session.add(dataset)
    db_session.flush()

    db_session.add_all(
        [
            PromptItem(
                dataset_id=dataset.id,
                prompt="Explain retrieval augmented generation in simple terms.",
                normalized_prompt="Explain retrieval augmented generation in simple terms.",
                category="explanation",
                difficulty="easy",
                expected_behavior="Explain the concept accurately for a beginner audience.",
                source="manual",
            ),
            PromptItem(
                dataset_id=dataset.id,
                prompt="Explain retrieval augmented generation in simple terms.",
                normalized_prompt="Explain retrieval augmented generation in simple terms.",
                category="explanation",
                difficulty="easy",
                expected_behavior="Explain the concept accurately for a beginner audience.",
                source="manual",
            ),
            PromptItem(
                dataset_id=dataset.id,
                prompt="Return valid JSON with title, owner, and risk from this incident report.",
                normalized_prompt="Return valid JSON with title, owner, and risk from this incident report.",
                category="structured_output",
                difficulty="medium",
                expected_behavior="Produce valid structured output using the requested keys only.",
                source="manual",
            ),
        ]
    )
    db_session.commit()

    service = DatasetCleaningService(db_session)
    service.settings.export_artifacts = False
    result = service.clean(dataset.id, semantic_threshold=0.98, remove_low_information=True)

    assert result["summary"]["removed_exact_duplicates"] == 1
    assert len(result["items"]) == 2


def test_scoring_service_creates_transparent_scores(db_session):
    dataset = Dataset(name="scoring-test", source="manual", status="generated")
    db_session.add(dataset)
    db_session.flush()

    db_session.add_all(
        [
            PromptItem(
                dataset_id=dataset.id,
                prompt="Write a Python function that validates a payload and list two edge cases.",
                normalized_prompt="Write a Python function that validates a payload and list two edge cases.",
                category="coding",
                difficulty="medium",
                expected_behavior="Return a correct function, explain the validation checks, and mention two edge cases.",
                source="manual",
            ),
            PromptItem(
                dataset_id=dataset.id,
                prompt="Summarize this report in exactly 3 bullets with risks and next steps.",
                normalized_prompt="Summarize this report in exactly 3 bullets with risks and next steps.",
                category="summarization",
                difficulty="medium",
                expected_behavior="Condense the report faithfully and highlight risks plus next actions.",
                source="manual",
            ),
        ]
    )
    db_session.commit()

    service = DatasetScoringService(db_session)
    service.settings.export_artifacts = False
    _dataset, scores, summary, _artifacts = service.score(dataset.id)

    assert len(scores) == 2
    assert all(isinstance(score, QualityScore) for score in scores)
    assert all(0.0 <= score.overall_score <= 1.0 for score in scores)
    assert "average_quality_score" in summary
    assert all(score.breakdown for score in scores)


def test_improvement_service_accepts_better_prompt_variant(db_session):
    dataset = Dataset(name="improvement-test", source="manual", status="generated")
    db_session.add(dataset)
    db_session.flush()

    weak_prompt = PromptItem(
        dataset_id=dataset.id,
        prompt="Explain stuff.",
        normalized_prompt="Explain stuff.",
        category="explanation",
        difficulty="easy",
        expected_behavior="Be good.",
        source="manual",
    )
    db_session.add(weak_prompt)
    db_session.commit()

    scoring_service = DatasetScoringService(db_session)
    scoring_service.settings.export_artifacts = False
    scoring_service.score(dataset.id)

    improvement_service = ImprovementService(db_session)
    records = improvement_service.improve(
        type(
            "Request",
            (),
            {
                "dataset_id": dataset.id,
                "quality_threshold": 0.99,
                "max_candidates": 5,
                "prefer_model_feedback": False,
            },
        )()
    )

    assert len(records) == 1
    assert records[0].score_after is not None
    assert records[0].score_after >= records[0].score_before

