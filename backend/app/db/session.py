from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.services.paths import get_data_dir, sqlite_url


def make_engine(database_url: str | None = None):
    url = database_url or sqlite_url(get_data_dir())
    eng = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    return eng


@contextmanager
def session_scope(database_url: str | None = None) -> Iterator[Session]:
    eng = make_engine(database_url)
    SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
