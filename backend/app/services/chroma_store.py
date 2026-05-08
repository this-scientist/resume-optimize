from __future__ import annotations

from pathlib import Path

import chromadb

from app.services.paths import get_data_dir

COLLECTION_NAME = "interview_knowledge"


def chroma_persist_path(data_dir: Path | None = None) -> Path:
    base = data_dir if data_dir is not None else get_data_dir()
    return base / "chroma"


def get_collection(data_dir: Path | None = None):
    path = chroma_persist_path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))
    return client.get_or_create_collection(COLLECTION_NAME)


def delete_by_source_id(data_dir: Path | None, source_id: int | str) -> None:
    coll = get_collection(data_dir)
    coll.delete(where={"source_id": str(source_id)})


def add_interview_chunks(
    data_dir: Path | None,
    *,
    texts: list[str],
    embeddings: list[list[float]],
    source_type: str,
    source_id: int | str,
) -> None:
    if len(texts) != len(embeddings):
        raise ValueError("texts and embeddings length mismatch")
    coll = get_collection(data_dir)
    sid = str(source_id)
    ids = [f"{sid}_{i}" for i in range(len(texts))]
    metadatas = [
        {"source_type": source_type, "source_id": sid, "chunk_index": i}
        for i in range(len(texts))
    ]
    coll.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def query_by_embedding(
    data_dir: Path | None,
    *,
    query_embedding: list[float],
    n_results: int,
    where: dict | None = None,
) -> dict:
    coll = get_collection(data_dir)
    return coll.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
