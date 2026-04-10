from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db


settings = get_settings()
configure_logging(settings.log_level)


def create_app() -> FastAPI:
    app = FastAPI(
        title="E.D.E.N. API",
        description="Evolving Dataset Evaluation Engine for LLM prompt datasets.",
        version="0.1.0",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    app.include_router(api_router)

    return app


app = create_app()
