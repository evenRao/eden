from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetDetail, DatasetSummaryResponse


router = APIRouter(tags=["datasets"])


@router.get("/datasets", response_model=list[DatasetSummaryResponse])
def list_datasets(db: Session = Depends(get_db)) -> list[DatasetSummaryResponse]:
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [
        DatasetSummaryResponse(
            dataset=dataset,
            item_count=len(dataset.prompt_items),
        )
        for dataset in datasets
    ]


@router.get("/datasets/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> DatasetDetail:
    dataset = (
        db.query(Dataset)
        .options(selectinload(Dataset.prompt_items))
        .filter(Dataset.id == dataset_id)
        .first()
    )
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} was not found.")
    return DatasetDetail.model_validate(dataset)

