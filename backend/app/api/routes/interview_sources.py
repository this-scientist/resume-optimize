from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import models
from app.deps import get_db
from app.schemas.interview_source import (
    BatchConfirmBody,
    DiscoverLinksBody,
    DiscoverLinksResponse,
    DiscoveredLinkOut,
    InterviewSourceBatchCreate,
    InterviewSourceConfirmResult,
    InterviewSourceCreate,
    InterviewSourceDetail,
    InterviewSourceRead,
)
from app.services import fetch_html
from app.services.crawl_pacing import CrawlPacingParams, gap_seconds_before_next_fetch
from app.services.discover_links import discover_links_for_url
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


def _require_embedding_model(settings: Settings) -> tuple[str, bool]:
    _, _, model = effective_embedding_config(settings)
    model = model.strip()
    if not model:
        raise HTTPException(
            status_code=400,
            detail="未配置 Embedding：请在环境变量或 settings.json 中设置 embedding_model（本地 BGE，如 BAAI/bge-small-zh-v1.5）",
        )
    return model, settings.embedding_use_fp16


def _dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in urls:
        u = raw.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def _dedupe_ints(ids: list[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for i in ids:
        if i in seen:
            continue
        seen.add(i)
        out.append(i)
    return out


@router.get("/", response_model=list[InterviewSourceRead])
def list_interview_sources(db: Session = Depends(get_db)):
    rows = db.scalars(select(models.InterviewSource).order_by(models.InterviewSource.created_at.desc())).all()
    return [_to_read(r) for r in rows]


@router.post("/discover-links", response_model=DiscoverLinksResponse)
async def discover_links_route(body: DiscoverLinksBody):
    base = str(body.url).strip()
    links, err = await discover_links_for_url(base, max_links=body.max_links)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return DiscoverLinksResponse(
        base_url=base,
        links=[DiscoveredLinkOut(url=x.url, label=x.label) for x in links],
    )


@router.post("/batch", response_model=list[InterviewSourceRead])
async def batch_create_interview_sources(
    body: InterviewSourceBatchCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    urls = _dedupe_urls(body.urls)
    if not urls:
        raise HTTPException(status_code=400, detail="没有有效 URL")
    pacing = CrawlPacingParams(
        chars_per_minute=settings.batch_crawl_chars_per_minute,
        min_delay_sec=settings.batch_crawl_min_delay_sec,
        max_delay_sec=settings.batch_crawl_max_delay_sec,
        jitter_ratio=settings.batch_crawl_jitter_ratio,
    )
    out: list[InterviewSourceRead] = []
    prev_chars = 0
    for i, u in enumerate(urls):
        if i > 0:
            wait_s = gap_seconds_before_next_fetch(prev_chars, pacing)
            await asyncio.sleep(wait_s)
        fr = await fetch_html.fetch_and_extract(u)
        fetch_ok = fr.ok
        prev_chars = len((fr.text or "").strip())
        src = models.InterviewSource(
            kind="url",
            url=u,
            title=fr.title,
            body_md=fr.text if fetch_ok else "",
            fetch_status="ok" if fetch_ok else "failed",
            index_status="pending",
        )
        db.add(src)
        db.flush()
        db.refresh(src)
        out.append(_to_read(src))
    return out


@router.post("/batch-confirm", response_model=list[InterviewSourceConfirmResult])
def batch_confirm_interview_sources(
    body: BatchConfirmBody,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    ids = _dedupe_ints(body.source_ids)
    model, use_fp16 = _require_embedding_model(settings)
    results: list[InterviewSourceConfirmResult] = []
    for sid in ids:
        src = db.get(models.InterviewSource, sid)
        if src is None:
            raise HTTPException(status_code=404, detail=f"interview source id={sid} not found")
        try:
            index_source(
                db,
                sid,
                model=model,
                use_fp16=use_fp16,
                data_dir=None,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"id {sid}: {exc}") from exc
        src = db.get(models.InterviewSource, sid)
        if src is None:
            raise HTTPException(status_code=404, detail="not found")
        results.append(InterviewSourceConfirmResult(id=src.id, index_status=src.index_status))
    return results


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
