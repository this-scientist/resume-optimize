# 本地简历优化助手 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本机 `127.0.0.1` 交付可运行的简历优化 Web：FastAPI 后端 + SQLite + Chroma 向量库 + Vite/React 前端；支持面试笔记入库（HTTP 抓取→确认→Embedding）、多简历 Markdown、岗位 JD（URL 抓取或粘贴）、岗位自定义面试阶段、关联简历后一键优化。

**Architecture:** 单一 Python 进程托管 API；结构化数据在 SQLite；面试知识经分块写入 Chroma（metadata 绑定 `interview_source.id`）；优化时将 **JD 全文** + **检索片段** + **简历全文** 通过 OpenAI 兼容客户端发往用户配置的 Chat API。前端以路由划分三大模块与设置页。

**Tech Stack:** Python 3.11+、FastAPI、Uvicorn、SQLAlchemy 2.x、SQLite、ChromaDB、httpx、trafilatura、OpenAI Python SDK（仅作兼容客户端）、Pydantic v2；前端 TypeScript、Vite、React 18、React Router、`@uiw/react-md-editor`。

---

## 仓库与目录约定（新建仓库）

以下路径均以仓库根目录 `<repo>/` 为基准创建。

```
<repo>/
  backend/
    pyproject.toml
    app/
      __init__.py
      main.py
      deps.py
      config.py
      db/
        base.py
        session.py
        models.py
      schemas/
        __init__.py
        resume.py
        job.py
        interview_source.py
        settings.py
        optimize.py
      services/
        paths.py
        fetch_html.py
        chunk_text.py
        token_budget.py
        embeddings.py
        chat_models.py
        chroma_store.py
        interview_index.py
        optimize_resume.py
      api/
        __init__.py
        router.py
        routes/
          health.py
          settings.py
          resumes.py
          jobs.py
          interview_sources.py
    tests/
      conftest.py
      test_fetch_html.py
      test_chunk_text.py
      test_token_budget.py
      test_api_health.py
      test_api_interview_flow.py
      test_optimize_resume.py
  frontend/
    package.json
    vite.config.ts
    tsconfig.json
    index.html
    src/
      main.tsx
      App.tsx
      api/client.ts
      routes.tsx
      pages/
        KnowledgePage.tsx
        ResumeListPage.tsx
        ResumeEditPage.tsx
        JobsPage.tsx
        JobDetailPage.tsx
        SettingsPage.tsx
      components/
        Disclaimer.tsx
  README.md
```

**说明：** `job_posting` 含 `current_stage_id`（可空 FK→`pipeline_stage`）；`interview_pipeline` 与岗位 **1:1**（`job_posting.pipeline_id`）。向量库 **仅索引面试来源正文**，不向量化 JD。

---

### Task 1: 后端脚手架与健康检查

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/api/router.py`
- Create: `backend/app/api/routes/health.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_api_health.py`

- [ ] **Step 1: Write失败的集成测试**

```python
# backend/tests/test_api_health.py
from fastapi.testclient import TestClient

from app.main import app


def test_health_ok():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 2: 运行测试确认失败**

Run（在 `backend/`）：`pytest tests/test_api_health.py -v`  
Expected：`ImportError` 或 `ModuleNotFoundError`（应用尚未创建）。

- [ ] **Step 3: 最小实现（pyproject + FastAPI 应用 + 路由）**

`backend/pyproject.toml`：

```toml
[project]
name = "resume-optimizer-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "httpx>=0.27.0"]

[build-system]
requires = ["setuptools>=68.0.0"]
build-backend = "setuptools.build_meta"
```

`backend/app/config.py`：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RESUME_OPTIMIZER_", env_file=".env", extra="ignore")
    host: str = "127.0.0.1"
    port: int = 8000


def get_settings() -> Settings:
    return Settings()
```

`backend/app/api/routes/health.py`：

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}
```

`backend/app/api/router.py`：

```python
from fastapi import APIRouter

from app.api.routes import health

api = APIRouter(prefix="/api")
api.include_router(health.router, tags=["health"])
```

`backend/app/main.py`：

```python
from fastapi import FastAPI

from app.api.router import api

app = FastAPI(title="Resume Optimizer Local")
app.include_router(api)
```

- [ ] **Step 4: 运行测试通过**

Run：`cd backend && python -m pip install -e ".[dev]" && pytest tests/test_api_health.py -v`  
Expected：`PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app backend/tests/test_api_health.py
git commit -m "feat(backend): scaffold FastAPI and health endpoint"
```

---

### Task 2: 用户数据目录与 SQLite 引擎（临时路径用于测试）

**Files:**
- Create: `backend/app/services/paths.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/tests/test_paths.py`

- [ ] **Step 1: 写失败单测（数据目录解析）**

```python
# backend/tests/test_paths.py
import os

from app.services.paths import get_data_dir


def test_data_dir_respects_env(tmp_path, monkeypatch):
    monkeypatch.setenv("RESUME_OPTIMIZER_DATA_DIR", str(tmp_path))
    d = get_data_dir()
    assert d == tmp_path.resolve()
    assert d.is_dir()
```

- [ ] **Step 2: 运行失败**  
Run：`pytest tests/test_paths.py -v` — Expected：`ImportError` 或函数不存在。

- [ ] **Step 3: 实现 `paths.py`**

```python
# backend/app/services/paths.py
from __future__ import annotations

import os
from pathlib import Path


def get_data_dir() -> Path:
    """
    本地用户数据根目录。优先环境变量 RESUME_OPTIMIZER_DATA_DIR；
    缺省为 macOS: ~/Library/Application Support/ResumeOptimizer
    其他平台: ~/.local/share/resume-optimizer
    """
    override = os.environ.get("RESUME_OPTIMIZER_DATA_DIR")
    if override:
        p = Path(override).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    home = Path.home()
    if (home / "Library" / "Application Support").exists():
        base = home / "Library" / "Application Support" / "ResumeOptimizer"
    else:
        base = home / ".local" / "share" / "resume-optimizer"
    base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


def sqlite_url(data_dir: Path) -> str:
    db_path = data_dir / "app.sqlite3"
    return f"sqlite:///{db_path.as_posix()}"
```

- [ ] **Step 4: 创建 SQLAlchemy engine/session 桩（下一 Task 接模型）**

`backend/app/db/base.py`：

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`backend/app/db/session.py`：

```python
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.services.paths import get_data_dir, sqlite_url


def make_engine(database_url: str | None = None):
    url = database_url or sqlite_url(get_data_dir())
    eng = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(bind=eng)
    return eng


def session_scope(database_url: str | None = None) -> Generator[Session, None, None]:
    eng = make_engine(database_url)
    SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

在 `test_paths.py` 末尾加入数据库创建烟雾测试（可选，或与 Task 3 合并）。

- [ ] **Step 5: 运行 `pytest tests/test_paths.py -v` PASS**

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/paths.py backend/app/db/base.py backend/app/db/session.py backend/tests/test_paths.py
git commit -m "feat(backend): user data dir and sqlite session helpers"
```

---

### Task 3: ORM 模型与 CRUD 骨架（简历 / 版本 / 岗位 / 流水线 / 面试来源）

**Files:**
- Create: `backend/app/db/models.py`
- Modify: `backend/app/db/session.py`（确保 `create_all` 在导入模型后调用）
- Create: `backend/tests/test_models_smoke.py`

**模型字段（与规格对齐，节选）：**

- `Resume`: id, title, category (String), current_body_md (Text), timestamps  
- `ResumeRevision`: id, resume_id FK, body_md, source (`user_edit`|`optimize`), job_id nullable, created_at  
- `JobPosting`: company, title, jd_source_url nullable, jd_text Text not null default "", jd_fetch_status (`ok`|`failed`), resume_id nullable, pipeline_id nullable, current_stage_id nullable  
- `InterviewPipeline`: id  
- `PipelineStage`: pipeline_id, name, sort_order  
- `InterviewSource`: kind (`url`|`manual_note`), url nullable, title nullable, body_md Text, fetch_status, created_at  

关系：`JobPosting.pipeline_id` → `InterviewPipeline.id`；`PipelineStage.pipeline_id` → `InterviewPipeline.id`；`JobPosting.current_stage_id` → `PipelineStage.id`。

- [ ] **Step 1: 模型冒烟测试**

```python
# backend/tests/test_models_smoke.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db import models  # noqa: F401  — registers mappers


def test_create_resume_and_revision(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'t.sqlite3'}", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        r = models.Resume(title="t", category="互联网", current_body_md="# Me")
        db.add(r)
        db.flush()
        rev = models.ResumeRevision(resume_id=r.id, body_md="# Me", source="user_edit")
        db.add(rev)
        db.commit()
        assert r.id is not None
```

- [ ] **Step 2: 运行失败** — `models` 未定义。

- [ ] **Step 3: 实现 `models.py`**（SQLAlchemy 2.0；以下为可直接粘贴的骨架，可按测试微调字段类型）

```python
# backend/app/db/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    category: Mapped[str] = mapped_column(String(64), default="未分类")
    current_body_md: Mapped[str] = mapped_column(Text, default="")
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
    jd_source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    jd_text: Mapped[str] = mapped_column(Text, default="")
    jd_fetch_status: Mapped[str] = mapped_column(String(16), default="failed")  # ok | failed
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    pipeline_id: Mapped[int | None] = mapped_column(ForeignKey("interview_pipelines.id", ondelete="SET NULL"), nullable=True)
    current_stage_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_stages.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
```

实现完成后扩展测试覆盖 `InterviewSource`、`JobPosting`+`InterviewPipeline`+`PipelineStage` 创建链。

- [ ] **Step 4: `pytest tests/test_models_smoke.py -v` PASS**

- [ ] **Step 5: Commit** — `feat(backend): add sqlalchemy models`

---

### Task 4: HTML 抓取与正文抽取服务

**Files:**
- Modify: `backend/pyproject.toml`（加入 `httpx`, `trafilatura`）
- Create: `backend/app/services/fetch_html.py`
- Create: `backend/tests/test_fetch_html.py`

- [ ] **Step 1: 单元测试（mock httpx）**

```python
# backend/tests/test_fetch_html.py
import httpx
import pytest

from app.services import fetch_html


@pytest.mark.asyncio
async def test_fetch_extract_title_and_text(monkeypatch):
    async def fake_get(url: str):
        class Resp:
            status_code = 200
            headers = {"content-type": "text/html; charset=utf-8"}
            text = "<html><body><article><p>你好世界</p></article></body></html>"

        return Resp()

    monkeypatch.setattr(fetch_html, "_get", fake_get)
    out = await fetch_html.fetch_and_extract("http://example.com/x")
    assert "你好世界" in out.text
    assert out.ok is True
```

- [ ] **Step 2: 运行失败**

- [ ] **Step 3: 实现 `fetch_html.py`**

要点：`httpx.AsyncClient(timeout=30)`；校验 `Content-Type` 含 `html`；`trafilatura.extract` 返回正文；正文长度 `<200` 字符判 `ok=False`（阈值可常量）；异常捕获返回 `ok=False` 与错误信息。

```python
# backend/app/services/fetch_html.py（结构与命名示意）
from dataclasses import dataclass
import trafilatura
import httpx


@dataclass
class FetchResult:
    ok: bool
    title: str | None
    text: str
    error: str | None = None


async def _get(url: str):
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        return await client.get(url)


async def fetch_and_extract(url: str) -> FetchResult:
    ...
```

- [ ] **Step 4: `pytest tests/test_fetch_html.py -v` PASS**

- [ ] **Step 5: Commit**

---

### Task 5: 文本分块与 token 预算

**Files:**
- Create: `backend/app/services/chunk_text.py`
- Create: `backend/app/services/token_budget.py`
- Create: `backend/tests/test_chunk_text.py`
- Create: `backend/tests/test_token_budget.py`

**策略（计划固定）：** 按段落 `\n\n` 切分；块最大约 **900 中文字符**（近似 token）；重叠 **80 字符**。`token_budget.py` 提供：给定检索片段列表与上限（如 4000 字），**先按相关度降序**（由调用方排序）**截断拼接**。

- [ ] **Step 1: 分块测试**

```python
from app.services.chunk_text import chunk_text

def test_chunk_preserves_order():
    s = "a" * 500 + "\n\n" + "b" * 500
    chunks = chunk_text(s, max_chars=400, overlap=50)
    assert len(chunks) >= 2
    assert chunks[0].startswith("a")
```

- [ ] **Step 2: 实现 `chunk_text.py`** — 返回 `list[str]`，每项带索引 metadata 由上层组装。

- [ ] **Step 3: `token_budget.py` 测试与实现** — `clip_chunks(chunks: list[str], max_chars: int) -> str`。

- [ ] **Step 4: pytest 全部 PASS**

- [ ] **Step 5: Commit**

---

### Task 6: Chroma 持久化与 Embedding 客户端

**Files:**
- Modify: `backend/pyproject.toml`：`chromadb`, `openai>=1.0.0`
- Create: `backend/app/services/chroma_store.py`
- Create: `backend/app/services/embeddings.py`
- Modify: `backend/app/config.py`：`embedding_base_url`, `embedding_api_key`, `embedding_model`（可选，默认值空）

**实现要点：**

- Chroma 持久化路径：`get_data_dir() / "chroma"`。
- 集合名：`interview_knowledge`。
- Metadata：`source_type` ∈ `interview_url`|`interview_note`，`source_id`（字符串），`chunk_index`（int）。
- `embeddings.py` 使用 `OpenAI(api_key=..., base_url=...).embeddings.create(model=..., input=batch)`；批量大小如 16；失败抛出由上层标记 `index_failed`。

- [ ] **Step 1: 使用 `pytest` + `monkeypatch` mock OpenAI client**，对 `embeddings.embed_chunks(["a","b"])` 返回假向量，写入临时 Chroma 路径。

- [ ] **Step 2: 实现文件**

- [ ] **Step 3: `pytest tests/test_chroma_embeddings.py`（新建）PASS**

- [ ] **Step 4: Commit**

---

### Task 7: 面试来源 API：预览 → 确认 → 建索引

**Files:**
- Create: `backend/app/schemas/interview_source.py`
- Create: `backend/app/services/interview_index.py`（`delete_by_source_id`, `index_source`）
- Create: `backend/app/api/routes/interview_sources.py`
- Modify: `backend/app/api/router.py` 注册路由
- Create: `backend/tests/test_api_interview_flow.py`

**端点：**

- `POST /api/interview-sources` body: `{ "url": "..." }` 或 `{ "note_text": "..." }`  
  - URL：调用 `fetch_and_extract`；存 `InterviewSource` `body_md` 为抽取文本，`fetch_status` 成功/失败。返回 `id` 与预览。  
  - 笔记：直接存 `kind=manual_note`，`fetch_status=ok`。
- `POST /api/interview-sources/{id}/confirm`：对 `body_md` 分块、Embedding、写入 Chroma；失败则 `fetch_status` 或独立字段标记 `index_status=failed`（实现可选列 `index_status` 或在 JSON 返回 error）。

为减少迁移，首版可在 `InterviewSource` 加 `index_status: str` 默认 `pending|indexed|failed`。

- [ ] **Step 1: 集成测试** 使用 `TestClient` + 临时 `RESUME_OPTIMIZER_DATA_DIR` + `httpx` mock 抓取成功。

- [ ] **Step 2: 实现路由与服务**

- [ ] **Step 3: `DELETE /api/interview-sources/{id}`** 删 DB 行并 `chroma_store.delete_where(source_id=...)`

- [ ] **Step 4: pytest PASS + Commit**

---

### Task 8: 简历与版本 API

**Files:**
- Create: `backend/app/schemas/resume.py`
- Create: `backend/app/api/routes/resumes.py`
- 覆盖：`GET/POST /api/resumes`，`GET/PATCH/DELETE /api/resumes/{id}`，`GET /api/resumes/{id}/revisions`，`POST /api/resumes/{id}/revisions/{rid}/restore`

**恢复逻辑：** 将 `ResumeRevision.body_md` 写回 `Resume.current_body_md`；**不**自动删后续版本（保持历史）。

- [ ] **TDD 小步**：先 `test_api_resumes.py` 再实现。

- [ ] **Commit**

---

### Task 9: 岗位、流水线与关联

**Files:**
- Create: `backend/app/schemas/job.py`
- Create: `backend/app/api/routes/jobs.py`

**端点：**

- `POST /api/jobs`：可选 `jd_source_url`；若有则 `fetch_and_extract`，失败则 `jd_fetch_status=failed` 且 `jd_text=""`，前端必须 PATCH 粘贴。  
- `PATCH /api/jobs/{id}`：`resume_id`, `jd_text`, `company`, `title`  
- `PUT /api/jobs/{id}/pipeline`：body `{ "stages": ["笔试","一面","二面"] }` —— 服务端替换该岗位 pipeline 的 stages（事务删除旧 stage、插入新 stage，`current_stage_id` 若失效则置第一阶或空）

- [ ] **测试**：创建 job → 设置 pipeline → 推进 `current_stage_id`

- [ ] **Commit**

---

### Task 10: 一键优化编排

**Files:**
- Create: `backend/app/schemas/optimize.py`
- Create: `backend/app/services/optimize_resume.py`
- Create: `backend/app/services/chat_models.py`（封装 Chat 完成）
- Create: `backend/tests/test_optimize_resume.py`（mock chat 与 embed）
- Create: `backend/app/api/routes/optimize.py` 或 挂在 `resumes` 的 `POST /api/resumes/{id}/optimize`

**请求体：**

```json
{ "job_id": 1, "top_k": 8, "extra_instructions": "强调性能优化" }
```

**服务端步骤：**

1. 读 `JobPosting.jd_text`，若空则 400。  
2. 用 `current_body_md` 作 query 文本，对 Chroma 做 **query（OpenAI embed query + chroma query）**；取 top_k。  
3. `token_budget.clip_chunks` 合并检索片段。  
4. 组装 system/user prompt（固定模板：输出 **完整 Markdown 简历**）。  
5. 调用 Chat；写入 `ResumeRevision` source=`optimize`，更新 `Resume.current_body_md`。  
6. 可选：写 `optimization_run` 行。

- [ ] **Step 1: 纯函数测试 prompt 组装长度**（不传真实 API）

- [ ] **Step 2: 集成测试 mock `chat_models.complete`**

- [ ] **Step 3: Commit**

---

### Task 11: 设置 API 与 Key 存储

**Files:**
- Create: `backend/app/schemas/settings.py`
- Create: `backend/app/api/routes/settings.py`  
- 存储：`get_data_dir() / "settings.json"`（明文字典：`chat_base_url`, `chat_api_key`, `chat_model`, `embedding_*`）

**GET** 返回时对 `api_key` 掩码末尾 4 位；**PUT** 接受完整替换。

- [ ] **测试：** PUT → GET 掩码一致

- [ ] **Commit**

---

### Task 12: 前端脚手架与 API 客户端

**Files:**
- Create: `frontend/package.json`, `vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`
- `vite.config.ts` 配置 `server.proxy`：`/api` → `http://127.0.0.1:8000`

`client.ts`：

```ts
const API = import.meta.env.VITE_API_BASE ?? "";
export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<T>;
}
```

- [ ] **Step 1: `pnpm install` / `npm install`；`npm run build` 成功**

- [ ] **Step 2: Commit**

---

### Task 13: 页面串联（最小可用 UI）

**Files:**
- Create: `frontend/src/routes.tsx`，页面组件 listed above  
- 每一页：调用对应 API；`/settings` 表单保存模型配置；`/knowledge` URL 输入→预览→确认；`/resumes` 列表→编辑（MD）；`/jobs` 列表→详情（JD 粘贴兜底、关联简历下拉、`PUT pipeline`）；简历详情页「一键优化」选 job。

- [ ] **在每个页面底部渲染 `Disclaimer`（固定版权声明文案）**

- [ ] **手动冒烟清单（记录在 README）**：抓取失败粘贴、优化生成新版本、pipeline 编辑。

- [ ] **Commit：`feat(frontend): MVP pages`**

---

### Task 14: README 与一键启动

**Files:**
- Create: `README.md`：后端 `uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend`；前端 `npm run dev`；环境变量说明；数据目录备份说明。

- [ ] **Commit**

---

## 计划自检（对照规格）

| 规格章节 | 计划任务 |
|---------|---------|
| 本地单用户、127.0.0.1、无鉴权 | Task 1 `config` 默认 host；README 启动参数 |
| 轻量 HTTP 抓取 | Task 4 |
| 面试知识向量、JD 全文进上下文 | Task 6–7、10 |
| 多简历 MD、分类仅归档 | Task 3、8、13 |
| 岗位 URL+粘贴、关联简历、自定义阶段 | Task 3、9、13 |
| 优化新版本+回滚 | Task 3、8、10 |
| 国内 API 兼容、设置页 | Task 10、11、13 |
| 错误与隐私（UI 免责、key 掩码） | Task 4 错误返回、Task 11 掩码、Task 13 Disclaimer |
| 测试策略 | 各 Task 含 pytest |

**占位符扫描：** 无 `TBD`；开放项（Chroma 选型）在 Task 6 已固定为 Chroma 持久化，与规格第 8 节一致。

---

## 执行方式（落地时二选一）

**计划已保存到 `docs/superpowers/plans/2026-05-08-resume-optimizer-local.md`。执行选项：**

1. **Subagent-Driven（推荐）** — 每个 Task 由新子代理执行，任务间人工/主代理复核，迭代快。需配合 **subagent-driven-development** 技能。  
2. **Inline Execution** — 在同一会话用 **executing-plans** 按检查点批量执行。

**你更倾向哪一种？** 若未指定，默认按 **1** 理解，由你或执行代理在开工时确认。
