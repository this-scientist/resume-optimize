from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.db import models
from app.services import chroma_store
from app.services.embeddings import embed_queries
from app.services.paths import get_data_dir
from app.services.token_budget import clip_chunks
from app.services.optimize_graph import run_optimize_graph
from app.services.user_config import effective_chat_config, effective_embedding_config

CLIP_MAX_CHARS = 4000


def build_optimize_user_message(
    jd_text: str,
    retrieved_context: str,
    resume_md: str,
    extra_instructions: str | None,
) -> str:
    parts = [
        "## 岗位 JD\n",
        jd_text.strip(),
        "\n\n## 检索到的面试相关知识（节选）\n",
        retrieved_context.strip() or "（无）",
        "\n\n## 当前简历（Markdown）\n",
        resume_md.strip(),
    ]
    if extra_instructions and extra_instructions.strip():
        parts.extend(["\n\n## 额外要求\n", extra_instructions.strip()])
    parts.append("\n\n请输出完整优化后的简历 Markdown 正文。")
    return "".join(parts)


def optimize_resume(
    db: Session,
    *,
    resume_id: int,
    job_id: int,
    top_k: int,
    extra_instructions: str | None,
    settings: Settings,
) -> models.ResumeRevision:
    resume = db.get(models.Resume, resume_id)
    if resume is None:
        raise ValueError("resume not found")
    job = db.get(models.JobPosting, job_id)
    if job is None:
        raise ValueError("job not found")

    jd = (job.jd_text or "").strip()
    if not jd:
        raise ValueError("job jd_text is empty")

    _, _, emb_model = effective_embedding_config(settings)
    emb_model = emb_model.strip()
    if not emb_model:
        raise ValueError("embedding not configured")

    chat_key, chat_base, chat_model = effective_chat_config(settings)
    if not chat_key or not chat_model:
        raise ValueError("chat not configured")

    query_text = (resume.current_body_md or "").strip() or jd[:800]
    qvec = embed_queries(
        [query_text],
        model=emb_model,
        use_fp16=settings.embedding_use_fp16,
    )[0]

    data_dir = get_data_dir()
    raw = chroma_store.query_by_embedding(
        data_dir,
        query_embedding=qvec,
        n_results=top_k,
        model_name=emb_model,
        where=None,
    )

    docs = (raw.get("documents") or [[]])[0] or []
    merged = clip_chunks(docs, CLIP_MAX_CHARS)

    body = run_optimize_graph(
        jd_text=jd,
        resume_md=resume.current_body_md or "",
        retrieved_context=merged,
        extra_instructions=extra_instructions,
        api_key=chat_key,
        base_url=chat_base,
        model=chat_model,
    )

    rev = models.ResumeRevision(
        resume_id=resume_id,
        body_md=body,
        source="optimize",
        job_id=job_id,
    )
    db.add(rev)
    resume.current_body_md = body
    db.flush()
    db.refresh(rev)
    return rev
