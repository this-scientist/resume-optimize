from __future__ import annotations

import os
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent


def _env_files() -> tuple[Path, ...]:
    """优先读取仓库根目录 .env，其次 backend/.env（与 uvicorn 工作目录无关）。"""
    return (
        _REPO_ROOT / ".env",
        _BACKEND_DIR / ".env",
    )


def _first_env(*keys: str) -> str:
    for k in keys:
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return ""


class Settings(BaseSettings):
    """
    应用配置。支持前缀 RESUME_OPTIMIZER_*；
    同时在未设置 Chat 专用项时，兼容常见别名（OPENAI_* / GLM_*）及 UVICORN_*。
    """

    model_config = SettingsConfigDict(
        env_prefix="RESUME_OPTIMIZER_",
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000
    db_mode: str = "local"

    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_use_fp16: bool = True

    chat_base_url: str = ""
    chat_api_key: str = ""
    chat_model: str = ""

    # 批量 URL 抓取「类人节奏」：上一页正文字符数 → 估算阅读时间 → 间隔 = 阅读时间/2（见 crawl_pacing）
    batch_crawl_chars_per_minute: float = Field(default=400.0, ge=60.0, le=8000.0)
    batch_crawl_min_delay_sec: float = Field(default=2.0, ge=0.5, le=120.0)
    batch_crawl_max_delay_sec: float = Field(default=120.0, ge=2.0, le=3600.0)
    batch_crawl_jitter_ratio: float = Field(default=0.1, ge=0.0, le=0.45)

    @model_validator(mode="after")
    def apply_env_aliases(self) -> Self:
        if not self.chat_api_key.strip():
            v = _first_env("OPENAI_API_KEY", "GLM_API_KEY")
            if v:
                object.__setattr__(self, "chat_api_key", v)

        if not self.chat_base_url.strip():
            v = _first_env(
                "OPENAI_BASE_URL",
                "GLM_BASE_URL",
                "OPENAI_API_BASE",
            )
            if v:
                object.__setattr__(self, "chat_base_url", v)

        if not self.chat_model.strip():
            v = _first_env("OPENAI_MODEL", "GLM_MODEL")
            if v:
                object.__setattr__(self, "chat_model", v)

        if not os.environ.get("RESUME_OPTIMIZER_HOST", "").strip():
            uv = _first_env("UVICORN_HOST")
            if uv:
                object.__setattr__(self, "host", uv)

        if not os.environ.get("RESUME_OPTIMIZER_PORT", "").strip():
            uvp = _first_env("UVICORN_PORT")
            if uvp:
                try:
                    object.__setattr__(self, "port", int(uvp))
                except ValueError:
                    pass

        dm = _first_env("RESUME_OPTIMIZER_DB_MODE", "DB_MODE")
        if dm:
            object.__setattr__(self, "db_mode", dm)

        return self


def get_settings() -> Settings:
    return Settings()
