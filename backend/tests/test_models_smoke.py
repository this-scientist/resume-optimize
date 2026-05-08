from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db import models  # noqa: F401  — registers mappers


def test_create_resume_and_revision(tmp_path):
    db_file = tmp_path / "t.sqlite3"
    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        r = models.Resume(title="t", category="互联网", current_body_md="# Me")
        db.add(r)
        db.flush()
        rev = models.ResumeRevision(resume_id=r.id, body_md="# Me", source="user_edit")
        db.add(rev)
        db.commit()
        assert r.id is not None


def test_create_interview_source(tmp_path):
    db_file = tmp_path / "t2.sqlite3"
    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        src = models.InterviewSource(
            kind="manual_note",
            url=None,
            title="一面记录",
            body_md="问了 Redis",
            fetch_status="ok",
            index_status="pending",
        )
        db.add(src)
        db.commit()
        assert src.id is not None


def test_job_posting_pipeline_chain(tmp_path):
    db_file = tmp_path / "t3.sqlite3"
    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        resume = models.Resume(title="我的简历", category="互联网", current_body_md="# X")
        db.add(resume)
        db.flush()

        pipeline = models.InterviewPipeline()
        db.add(pipeline)
        db.flush()

        stage1 = models.PipelineStage(pipeline_id=pipeline.id, name="笔试", sort_order=0)
        stage2 = models.PipelineStage(pipeline_id=pipeline.id, name="一面", sort_order=1)
        db.add_all([stage1, stage2])
        db.flush()

        job = models.JobPosting(
            company="Acme",
            title="后端",
            jd_text="负责 API",
            jd_fetch_status="ok",
            resume_id=resume.id,
            pipeline_id=pipeline.id,
            current_stage_id=stage2.id,
        )
        db.add(job)
        db.commit()

        assert pipeline.id is not None
        assert job.id is not None
        assert job.current_stage_id == stage2.id
