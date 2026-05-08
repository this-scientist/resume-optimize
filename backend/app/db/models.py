from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    category: Mapped[str] = mapped_column(String(64), default="未分类")
    current_body_md: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InterviewPipeline(Base):
    __tablename__ = "interview_pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("interview_pipelines.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    salary: Mapped[str] = mapped_column(String(128), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    jd_source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    jd_text: Mapped[str] = mapped_column(Text, default="")
    jd_fetch_status: Mapped[str] = mapped_column(String(16), default="failed")  # ok | failed
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    pipeline_id: Mapped[int | None] = mapped_column(ForeignKey("interview_pipelines.id", ondelete="SET NULL"), nullable=True)
    current_stage_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_stages.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResumeRevision(Base):
    __tablename__ = "resume_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    body_md: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="user_edit")  # user_edit | optimize
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InterviewSource(Base):
    __tablename__ = "interview_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(16), default="url")  # url | manual_note
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body_md: Mapped[str] = mapped_column(Text, default="")
    fetch_status: Mapped[str] = mapped_column(String(16), default="ok")
    index_status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | indexed | failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
