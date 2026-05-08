from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.db import models
from app.services import chroma_store
from app.services.embeddings import embed_chunks
from app.services.paths import get_data_dir
from app.services.token_budget import clip_chunks
from app.services.chat_models import complete_chat
from app.services.user_config import effective_chat_config, effective_embedding_config

SYSTEM_PROMPT = """你是一名中文简历优化助手。根据岗位描述 JD、检索到的面试相关知识片段与用户当前简历 Markdown，
输出一版完整、可直接投递的新简历正文（Markdown）。
保持事实一致，可强化措辞与结构；不要编造未经历的项目。"""

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

    emb_key, emb_base, emb_model = effective_embedding_config(settings)
    if not emb_key or not emb_model:
        raise ValueError("embedding not configured")

    chat_key, chat_base, chat_model = effective_chat_config(settings)
    if not chat_key or not chat_model:
        raise ValueError("chat not configured")

    query_text = (resume.current_body_md or "").strip() or jd[:800]
    qvec = embed_chunks([query_text], api_key=emb_key, base_url=emb_base, model=emb_model)[0]

    data_dir = get_data_dir()
    raw = chroma_store.query_by_embedding(
        data_dir,
        query_embedding=qvec,
        n_results=top_k,
        where=None,
    )

    docs = (raw.get("documents") or [[]])[0] or []
    merged = clip_chunks(docs, CLIP_MAX_CHARS)

    user_msg = build_optimize_user_message(jd, merged, resume.current_body_md or "", extra_instructions)

    body = complete_chat(
        system=SYSTEM_PROMPT,
        user=user_msg,
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
