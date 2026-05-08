from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobCreate(BaseModel):
    """仅从 JD 页面 URL 抓取并新建岗位；公司/职位/薪资/发布时间由服务端解析。"""

    jd_source_url: str = Field(..., min_length=12)
    resume_id: int | None = None

    @field_validator("jd_source_url")
    @classmethod
    def must_be_http(cls, v: str) -> str:
        u = v.strip()
        if not u.startswith(("http://", "https://")):
            raise ValueError("jd_source_url 须为 http(s) 链接")
        return u


class JobPatch(BaseModel):
    company: str | None = None
    title: str | None = None
    salary: str | None = None
    published_at: datetime | None = None
    jd_text: str | None = None
    jd_source_url: str | None = None
    jd_fetch_status: str | None = None
    resume_id: int | None = None
    current_stage_id: int | None = None

    @field_validator("jd_source_url")
    @classmethod
    def jd_url_optional(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            return None
        if not s.startswith(("http://", "https://")):
            raise ValueError("jd_source_url 须为 http(s) 链接或留空")
        return s

    @field_validator("jd_fetch_status")
    @classmethod
    def fetch_status_enum(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in ("ok", "failed"):
            raise ValueError("jd_fetch_status 只能为 ok 或 failed")
        return v


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
    salary: str
    published_at: datetime | None
    jd_source_url: str | None
    jd_text: str
    jd_fetch_status: str
    resume_id: int | None
    pipeline_id: int | None
    current_stage_id: int | None
    created_at: datetime
    updated_at: datetime
