from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dataset import (
    CleanDatasetRequest,
    DatasetStageResponse,
    GenerateDatasetRequest,
    ScoreDatasetRequest,
)
from app.schemas.evaluation import EvaluateDatasetRequest, EvaluateDatasetResponse
from app.schemas.improvement import ImproveDatasetRequest, ImproveDatasetResponse
from app.schemas.scoring import QualityScoreRead, ScoreDatasetResponse
from app.services.cleaning_service import DatasetCleaningService
from app.services.evaluation_service import EvaluationService
from app.services.generation_service import DatasetGenerationService
from app.services.improvement_service import ImprovementService
from app.services.scoring_service import DatasetScoringService


router = APIRouter(tags=["pipeline"])


@router.post("/generate-dataset", response_model=DatasetStageResponse)
def generate_dataset(
    request: GenerateDatasetRequest,
    db: Session = Depends(get_db),
) -> DatasetStageResponse:
    try:
        dataset, items, artifacts = DatasetGenerationService(db).generate(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DatasetStageResponse(
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        status=dataset.status,
        item_count=len(items),
        artifacts=artifacts,
        message="Dataset generated successfully.",
    )


@router.post("/clean", response_model=DatasetStageResponse)
def clean_dataset(
    request: CleanDatasetRequest,
    db: Session = Depends(get_db),
) -> DatasetStageResponse:
    try:
        result = DatasetCleaningService(db).clean(
            dataset_id=request.dataset_id,
            semantic_threshold=request.semantic_threshold,
            remove_low_information=request.remove_low_information,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    dataset = result["dataset"]
    items = result["items"]
    return DatasetStageResponse(
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        status=dataset.status,
        item_count=len(items),
        artifacts=result["artifacts"],
        message="Dataset cleaned successfully.",
    )


@router.post("/score", response_model=ScoreDatasetResponse)
def score_dataset(
    request: ScoreDatasetRequest,
    db: Session = Depends(get_db),
) -> ScoreDatasetResponse:
    try:
        dataset, score_rows, summary, _artifacts = DatasetScoringService(db).score(
            request.dataset_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ScoreDatasetResponse(
        dataset_id=dataset.id,
        average_quality_score=summary["average_quality_score"],
        score_count=len(score_rows),
        item_scores=[QualityScoreRead.model_validate(score) for score in score_rows],
        summary=summary,
    )


@router.post("/evaluate", response_model=EvaluateDatasetResponse)
def evaluate_dataset(
    request: EvaluateDatasetRequest,
    db: Session = Depends(get_db),
) -> EvaluateDatasetResponse:
    try:
        runs = EvaluationService(db).evaluate(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return EvaluateDatasetResponse(
        dataset_id=request.dataset_id,
        run_ids=[run.id for run in runs],
        evaluations=runs,
    )


@router.post("/improve", response_model=ImproveDatasetResponse)
def improve_dataset(
    request: ImproveDatasetRequest,
    db: Session = Depends(get_db),
) -> ImproveDatasetResponse:
    try:
        records = ImprovementService(db).improve(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ImproveDatasetResponse(
        dataset_id=request.dataset_id,
        attempted=len(records),
        accepted=sum(1 for record in records if record.accepted),
        improvements=records,
    )

