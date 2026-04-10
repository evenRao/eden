from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.monitoring.aggregator import MetricsAggregator
from app.schemas.metrics import MetricSnapshotRead, MetricsResponse


router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(dataset_id: str | None = None, db: Session = Depends(get_db)) -> MetricsResponse:
    result = MetricsAggregator(db).collect(dataset_id=dataset_id, persist_snapshot=True)
    return MetricsResponse(
        dataset_metrics=result["dataset_metrics"],
        model_metrics=result["model_metrics"],
        trend_snapshots=[
            MetricSnapshotRead.model_validate(snapshot) for snapshot in result["trend_snapshots"]
        ],
    )

