from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import models
from app.deps import get_db
from app.schemas.interview_source import (
    InterviewSourceConfirmResult,
    InterviewSourceCreate,
    InterviewSourceDetail,
    InterviewSourceRead,
)
from app.services import fetch_html
from app.services.interview_index import delete_by_source_id as chroma_delete_source
from app.services.interview_index import index_source
from app.services.paths import get_data_dir
from app.services.user_config import effective_embedding_config

router = APIRouter(prefix="/interview-sources", tags=["interview-sources"])


PREVIEW_LEN = 4000


def _preview(body: str) -> str:
    if len(body) <= PREVIEW_LEN:
        return body
    return body[:PREVIEW_LEN] + "…"


def _to_read(src: models.InterviewSource) -> InterviewSourceRead:
    return InterviewSourceRead(
        id=src.id,
        kind=src.kind,
        url=src.url,
        title=src.title,
        body_preview=_preview(src.body_md or ""),
        fetch_status=src.fetch_status,
        index_status=src.index_status,
        created_at=src.created_at,
        embedding_model=src.embedding_model,
    )


@router.get("/", response_model=list[InterviewSourceRead])
def list_interview_sources(db: Session = Depends(get_db)):
    rows = db.scalars(select(models.InterviewSource).order_by(models.InterviewSource.created_at.desc())).all()
    return [_to_read(r) for r in rows]


@router.post("/", response_model=InterviewSourceRead)
async def create_interview_source(
    body: InterviewSourceCreate,
    db: Session = Depends(get_db),
):
    if body.note_text is not None:
        src = models.InterviewSource(
            kind="manual_note",
            url=None,
            title=None,
            body_md=body.note_text,
            fetch_status="ok",
            index_status="pending",
        )
        db.add(src)
        db.flush()
        db.refresh(src)
        return _to_read(src)

    fr = await fetch_html.fetch_and_extract(body.url or "")
    fetch_ok = fr.ok
    src = models.InterviewSource(
        kind="url",
        url=str(body.url),
        title=fr.title,
        body_md=fr.text if fetch_ok else "",
        fetch_status="ok" if fetch_ok else "failed",
        index_status="pending",
    )
    db.add(src)
    db.flush()
    db.refresh(src)
    return _to_read(src)


@router.post("/{source_id}/confirm", response_model=InterviewSourceConfirmResult)
def confirm_interview_source(
    source_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    src = db.get(models.InterviewSource, source_id)
    if src is None:
        raise HTTPException(status_code=404, detail="not found")

    model, use_fp16 = _require_embedding_model(settings)

    try:
        index_source(
            db,
            source_id,
            model=model,
            use_fp16=use_fp16,
            data_dir=None,
        )
    except Exception as exc:
        db.rollback()
        src = db.get(models.InterviewSource, source_id)
        if src is not None:
            src.index_status = "failed"
            db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    src = db.get(models.InterviewSource, source_id)
    if src is None:
        raise HTTPException(status_code=404, detail="not found")
    return InterviewSourceConfirmResult(id=src.id, index_status=src.index_status)


@router.get("/{source_id}", response_model=InterviewSourceDetail)
def get_interview_source(source_id: int, db: Session = Depends(get_db)):
    src = db.get(models.InterviewSource, source_id)
    if src is None:
        raise HTTPException(status_code=404, detail="not found")
    return InterviewSourceDetail(
        id=src.id,
        kind=src.kind,
        url=src.url,
        title=src.title,
        body_md=src.body_md or "",
        fetch_status=src.fetch_status,
        index_status=src.index_status,
        created_at=src.created_at,
        embedding_model=src.embedding_model,
    )


def _require_embedding_model(settings: Settings) -> tuple[str, bool]:
    _, _, model = effective_embedding_config(settings)
    model = model.strip()
    if not model:
        raise HTTPException(
            status_code=400,
            detail="未配置 Embedding：请在环境变量或 settings.json 中设置 embedding_model（本地 BGE，如 BAAI/bge-small-zh-v1.5）",
        )
    return model, settings.embedding_use_fp16


@router.delete("/{source_id}", status_code=204)
def delete_interview_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    src = db.get(models.InterviewSource, source_id)
    if src is None:
        raise HTTPException(status_code=404, detail="not found")

    data_dir = get_data_dir()
    try:
        chroma_delete_source(
            source_id,
            data_dir=data_dir,
            embedding_model=src.embedding_model,
        )
    except Exception:
        pass

    db.delete(src)
    db.commit()
    return None
