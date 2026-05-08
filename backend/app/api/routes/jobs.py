from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import models
from app.deps import get_db
from app.schemas.job import JobCreate, JobPatch, JobRead, PipelinePut
from app.services import fetch_html
from app.services.job_metadata import parse_job_fields

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[JobRead])
def list_jobs(db: Session = Depends(get_db)):
    stmt = select(models.JobPosting).order_by(models.JobPosting.updated_at.desc())
    return list(db.scalars(stmt).all())


@router.post("/", response_model=JobRead)
async def create_job(body: JobCreate, db: Session = Depends(get_db)):
    url = body.jd_source_url
    fr = await fetch_html.fetch_and_extract(url, retain_html=True)

    hints = parse_job_fields(fr.raw_html or "", fr.text, fr.title)
    company = hints.company
    title = hints.job_title or (fr.title or "")[:255]

    if fr.ok:
        jd_text = fr.text
        jd_fetch_status = "ok"
    else:
        jd_text = fr.text or ""
        jd_fetch_status = "failed"

    job = models.JobPosting(
        company=company,
        title=title,
        salary=hints.salary,
        published_at=hints.published_at,
        jd_source_url=url,
        jd_text=jd_text,
        jd_fetch_status=jd_fetch_status,
        resume_id=body.resume_id,
    )
    db.add(job)
    db.flush()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(models.JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="not found")
    return job


@router.patch("/{job_id}", response_model=JobRead)
def patch_job(job_id: int, body: JobPatch, db: Session = Depends(get_db)):
    job = db.get(models.JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(job, k, v)
    db.flush()
    db.refresh(job)
    return job


@router.put("/{job_id}/pipeline", response_model=JobRead)
def put_pipeline(job_id: int, body: PipelinePut, db: Session = Depends(get_db)):
    job = db.get(models.JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="not found")

    if job.pipeline_id is None:
        pipe = models.InterviewPipeline()
        db.add(pipe)
        db.flush()
        job.pipeline_id = pipe.id

    db.execute(
        delete(models.PipelineStage).where(models.PipelineStage.pipeline_id == job.pipeline_id)
    )

    new_ids: list[int] = []
    for i, name in enumerate(body.stages):
        st = models.PipelineStage(pipeline_id=job.pipeline_id, name=name, sort_order=i)
        db.add(st)
        db.flush()
        new_ids.append(st.id)

    if new_ids:
        if job.current_stage_id is None or job.current_stage_id not in new_ids:
            job.current_stage_id = new_ids[0]
    else:
        job.current_stage_id = None

    db.flush()
    db.refresh(job)
    return job
