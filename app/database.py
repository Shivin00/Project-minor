from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def _prepare_sqlite_path(database_url: str) -> None:
    if database_url.startswith("sqlite:///./"):
        relative_path = database_url.replace("sqlite:///./", "", 1)
        Path(relative_path).parent.mkdir(parents=True, exist_ok=True)
        return
    if database_url.startswith("sqlite:////"):
        absolute_path = database_url.replace("sqlite:////", "", 1)
        Path(f"/{absolute_path}").parent.mkdir(parents=True, exist_ok=True)


if settings.database_url.startswith("sqlite"):
    _prepare_sqlite_path(settings.database_url)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
