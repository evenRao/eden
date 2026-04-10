from fastapi import APIRouter

from app.api.routes.datasets import router as datasets_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.pipeline import router as pipeline_router
from app.api.routes.runs import router as runs_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(pipeline_router)
api_router.include_router(metrics_router)
api_router.include_router(datasets_router)
api_router.include_router(runs_router)

