from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.services.paths import get_data_dir, sqlite_url

import app.db.models  # noqa: F401  — register ORM mappers with Base.metadata


def _ensure_sqlite_job_posting_columns(engine) -> None:
    """旧版 SQLite 在加模型列后不会自动 ALTER，补全 job_postings 列。"""
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        r = conn.execute(text("PRAGMA table_info(job_postings)"))
        existing = {row[1] for row in r.fetchall()}
        if not existing:
            return
        if "salary" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE job_postings ADD COLUMN salary VARCHAR(128) NOT NULL DEFAULT ''"
                )
            )
        if "published_at" not in existing:
            conn.execute(
                text("ALTER TABLE job_postings ADD COLUMN published_at DATETIME")
            )


def make_engine(database_url: str | None = None):
    url = database_url or sqlite_url(get_data_dir())
    eng = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    _ensure_sqlite_job_posting_columns(eng)
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
