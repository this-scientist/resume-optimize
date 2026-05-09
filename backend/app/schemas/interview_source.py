from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InterviewSourceCreate(BaseModel):
    url: str | None = None
    note_text: str | None = Field(None, description="手动笔记正文 Markdown")

    @model_validator(mode="after")
    def exactly_one_source(self) -> InterviewSourceCreate:
        has_url = self.url is not None and str(self.url).strip() != ""
        has_note = self.note_text is not None
        if has_url == has_note:
            raise ValueError("必须且只能提供 url 或 note_text 之一")
        return self


class InterviewSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    url: str | None
    title: str | None
    body_preview: str
    fetch_status: str
    index_status: str
    created_at: datetime
    embedding_model: str | None = None


class InterviewSourceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    url: str | None
    title: str | None
    body_md: str
    fetch_status: str
    index_status: str
    created_at: datetime
    embedding_model: str | None = None


class InterviewSourceConfirmResult(BaseModel):
    id: int
    index_status: str
    detail: str | None = None


class DiscoverLinksBody(BaseModel):
    url: str = Field(..., min_length=4)
    max_links: int = Field(80, ge=10, le=200)


class DiscoveredLinkOut(BaseModel):
    url: str
    label: str | None = None


class DiscoverLinksResponse(BaseModel):
    base_url: str
    links: list[DiscoveredLinkOut]


class InterviewSourceBatchCreate(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=60)


class BatchConfirmBody(BaseModel):
    source_ids: list[int] = Field(..., min_length=1, max_length=60)
