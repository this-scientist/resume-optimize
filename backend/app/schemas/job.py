from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    company: str = ""
    title: str = ""
    jd_source_url: str | None = None
    resume_id: int | None = None


class JobPatch(BaseModel):
    company: str | None = None
    title: str | None = None
    jd_text: str | None = None
    resume_id: int | None = None
    current_stage_id: int | None = None


class PipelinePut(BaseModel):
    stages: list[str] = Field(default_factory=list)


class PipelineStageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pipeline_id: int
    name: str
    sort_order: int


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    title: str
    jd_source_url: str | None
    jd_text: str
    jd_fetch_status: str
    resume_id: int | None
    pipeline_id: int | None
    current_stage_id: int | None
    created_at: datetime
    updated_at: datetime
