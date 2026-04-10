from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.evaluation import EvaluationRun
from app.schemas.evaluation import EvaluationRunRead


router = APIRouter(tags=["runs"])


@router.get("/runs", response_model=list[EvaluationRunRead])
def list_runs(dataset_id: str | None = None, db: Session = Depends(get_db)) -> list[EvaluationRunRead]:
    query = db.query(EvaluationRun).options(selectinload(EvaluationRun.model_outputs))
    if dataset_id:
        query = query.filter(EvaluationRun.dataset_id == dataset_id)
    runs = query.order_by(EvaluationRun.created_at.desc()).all()
    return [EvaluationRunRead.model_validate(run) for run in runs]

