from __future__ import annotations

from pydantic import BaseModel, Field


class OptimizeBody(BaseModel):
    job_id: int = Field(..., ge=1)
    top_k: int = Field(8, ge=1, le=50)
    extra_instructions: str | None = None


class OptimizeResult(BaseModel):
    revision_id: int
    resume_id: int
