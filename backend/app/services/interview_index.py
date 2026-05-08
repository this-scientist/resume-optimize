from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.db import models
from app.services import chroma_store
from app.services.chunk_text import chunk_text
from app.services.embeddings import embed_corpus


def delete_by_source_id(
    source_id: int | str,
    *,
    data_dir: Path | None = None,
    embedding_model: str | None = None,
) -> None:
    chroma_store.delete_by_source_id(data_dir, source_id, embedding_model)


def index_source(
    db: Session,
    source_id: int,
    *,
    model: str,
    use_fp16: bool = True,
    data_dir: Path | None = None,
) -> None:
    src = db.get(models.InterviewSource, source_id)
    if src is None:
        raise ValueError("interview source not found")
    text = (src.body_md or "").strip()
    if not text:
        raise ValueError("empty body_md")

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("no chunks produced")

    vectors = embed_corpus(chunks, model=model, use_fp16=use_fp16)

    chroma_store.delete_by_source_id(data_dir, source_id, src.embedding_model)

    source_type = "interview_url" if src.kind == "url" else "interview_note"
    chroma_store.add_interview_chunks(
        data_dir,
        texts=chunks,
        embeddings=vectors,
        source_type=source_type,
        source_id=source_id,
        model_name=model,
    )

    src.index_status = "indexed"
    src.embedding_model = model.strip()
