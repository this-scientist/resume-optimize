from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreate(BaseModel):
    title: str = ""
    category: str = "未分类"
    current_body_md: str = ""


class ResumeUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    current_body_md: str | None = None


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    current_body_md: str
    created_at: datetime
    updated_at: datetime


class ResumeRevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    body_md: str
    source: str
    job_id: int | None
    created_at: datetime
