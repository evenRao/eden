from datetime import datetime

from pydantic import Field

from app.schemas.common import EDENBaseModel


class MetricSnapshotRead(EDENBaseModel):
    id: str
    dataset_id: str | None = None
    snapshot_type: str
    payload: dict
    created_at: datetime
    updated_at: datetime


class MetricsResponse(EDENBaseModel):
    dataset_metrics: dict = Field(default_factory=dict)
    model_metrics: list[dict] = Field(default_factory=list)
    trend_snapshots: list[MetricSnapshotRead] = Field(default_factory=list)

