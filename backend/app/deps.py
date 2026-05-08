from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import session_scope


def get_db() -> Generator[Session, None, None]:
    with session_scope() as db:
        yield db
