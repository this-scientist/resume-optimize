from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import models
from app.deps import get_db
from app.schemas.optimize import OptimizeBody, OptimizeResult
from app.schemas.resume import ResumeCreate, ResumeRead, ResumeRevisionRead, ResumeUpdate
from app.services.optimize_resume import optimize_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("/", response_model=list[ResumeRead])
def list_resumes(db: Session = Depends(get_db)):
    stmt = select(models.Resume).order_by(models.Resume.updated_at.desc())
    return list(db.scalars(stmt).all())


@router.post("/", response_model=ResumeRead)
def create_resume(body: ResumeCreate, db: Session = Depends(get_db)):
    r = models.Resume(
        title=body.title,
        category=body.category,
        current_body_md=body.current_body_md,
    )
    db.add(r)
    db.flush()
    db.refresh(r)
    return r


@router.get("/{resume_id}", response_model=ResumeRead)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    r = db.get(models.Resume, resume_id)
    if r is None:
        raise HTTPException(status_code=404, detail="not found")
    return r


@router.patch("/{resume_id}", response_model=ResumeRead)
def patch_resume(resume_id: int, body: ResumeUpdate, db: Session = Depends(get_db)):
    r = db.get(models.Resume, resume_id)
    if r is None:
        raise HTTPException(status_code=404, detail="not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(r, k, v)
    db.flush()
    db.refresh(r)
    return r


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    r = db.get(models.Resume, resume_id)
    if r is None:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(r)
    return None


@router.get("/{resume_id}/revisions", response_model=list[ResumeRevisionRead])
def list_revisions(resume_id: int, db: Session = Depends(get_db)):
    if db.get(models.Resume, resume_id) is None:
        raise HTTPException(status_code=404, detail="not found")
    stmt = (
        select(models.ResumeRevision)
        .where(models.ResumeRevision.resume_id == resume_id)
        .order_by(models.ResumeRevision.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("/{resume_id}/revisions/{revision_id}/restore", response_model=ResumeRead)
def restore_revision(resume_id: int, revision_id: int, db: Session = Depends(get_db)):
    resume = db.get(models.Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="resume not found")
    rev = db.get(models.ResumeRevision, revision_id)
    if rev is None or rev.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="revision not found")
    resume.current_body_md = rev.body_md
    db.flush()
    db.refresh(resume)
    return resume


@router.post("/{resume_id}/optimize", response_model=OptimizeResult)
def optimize(
    resume_id: int,
    body: OptimizeBody,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        rev = optimize_resume(
            db,
            resume_id=resume_id,
            job_id=body.job_id,
            top_k=body.top_k,
            extra_instructions=body.extra_instructions,
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OptimizeResult(revision_id=rev.id, resume_id=resume_id)
