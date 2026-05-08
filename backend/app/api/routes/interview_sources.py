from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import models
from app.deps import get_db
from app.schemas.interview_source import (
    InterviewSourceConfirmResult,
    InterviewSourceCreate,
    InterviewSourceRead,
)
from app.services import fetch_html
from app.services.interview_index import delete_by_source_id as chroma_delete_source
from app.services.interview_index import index_source
from app.services.paths import get_data_dir
from app.services.settings_file import load_settings_json

router = APIRouter()


PREVIEW_LEN = 4000


def _preview(body: str) -> str:
    if len(body) <= PREVIEW_LEN:
        return body
    return body[:PREVIEW_LEN] + "…"


def _embedding_triplet(settings: Settings) -> tuple[str, str | None, str]:
    j = load_settings_json()
    api_key = (j.get("embedding_api_key") or "").strip() or settings.embedding_api_key
    base_raw = (j.get("embedding_base_url") or "").strip() or settings.embedding_base_url
    model = (j.get("embedding_model") or "").strip() or settings.embedding_model
    base_url = base_raw or None
    return api_key, base_url, model


def _require_embedding(settings: Settings) -> tuple[str, str | None, str]:
    api_key, base_url, model = _embedding_triplet(settings)
    if not api_key.strip() or not model.strip():
        raise HTTPException(status_code=400, detail="未配置 Embedding：请在环境变量或 settings.json 中设置 embedding_api_key 与 embedding_model")
    return api_key, base_url, model


@router.post("/interview-sources", response_model=InterviewSourceRead)
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
        return InterviewSourceRead(
            id=src.id,
            kind=src.kind,
            url=src.url,
            title=src.title,
            body_preview=_preview(src.body_md),
            fetch_status=src.fetch_status,
            index_status=src.index_status,
        )

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
    return InterviewSourceRead(
        id=src.id,
        kind=src.kind,
        url=src.url,
        title=src.title,
        body_preview=_preview(src.body_md),
        fetch_status=src.fetch_status,
        index_status=src.index_status,
    )


@router.post("/interview-sources/{source_id}/confirm", response_model=InterviewSourceConfirmResult)
def confirm_interview_source(
    source_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    src = db.get(models.InterviewSource, source_id)
    if src is None:
        raise HTTPException(status_code=404, detail="not found")

    api_key, base_url, model = _require_embedding(settings)

    try:
        index_source(
            db,
            source_id,
            api_key=api_key,
            base_url=base_url,
            model=model,
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


@router.delete("/interview-sources/{source_id}", status_code=204)
def delete_interview_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    src = db.get(models.InterviewSource, source_id)
    if src is None:
        raise HTTPException(status_code=404, detail="not found")

    data_dir = get_data_dir()
    try:
        chroma_delete_source(source_id, data_dir=data_dir)
    except Exception:
        pass

    db.delete(src)
    db.commit()
    return None
