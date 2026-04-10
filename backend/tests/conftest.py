import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import get_settings
from app.models.base import Base


@pytest.fixture
def db_session(tmp_path):
    database_path = tmp_path / "eden_test.db"
    os.environ["EDEN_EXPORT_ARTIFACTS"] = "false"
    os.environ["EDEN_DATABASE_URL"] = f"sqlite:///{database_path}"
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        get_settings.cache_clear()

