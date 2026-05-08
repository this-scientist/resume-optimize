from __future__ import annotations

import re
import threading
from pathlib import Path

import chromadb

from app.services.paths import get_data_dir

# Chroma 1.x 在同一进程内多次 new PersistentClient(同一路径) 会触发 SharedSystemClient 内部 KeyError，
# 因此对每个持久化目录只保留一个客户端实例。
_CLIENT_LOCK = threading.Lock()
_CLIENTS: dict[str, chromadb.PersistentClient] = {}

# 旧版固定集合名（首版未按模型分集合）；向量维度由首次写入决定，换模型后须用新集合。
LEGACY_COLLECTION_NAME = "interview_knowledge"


def chroma_persist_path(data_dir: Path | None = None) -> Path:
    base = data_dir if data_dir is not None else get_data_dir()
    return base / "chroma"


def _collection_name_for_model(model_name: str) -> str:
    """按嵌入模型划分 Chroma 集合，避免不同维度写入同一集合。"""
    s = model_name.strip()
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", s)
    safe = safe.strip("_")[:200] or "default"
    return f"interview_knowledge__{safe}"


def _client(data_dir: Path | None) -> chromadb.PersistentClient:
    path = chroma_persist_path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    key = str(path.resolve())
    with _CLIENT_LOCK:
        if key not in _CLIENTS:
            _CLIENTS[key] = chromadb.PersistentClient(path=key)
        return _CLIENTS[key]


def get_collection(data_dir: Path | None, model_name: str):
    """获取当前嵌入模型对应的集合（维度由首次 add 固定）。"""
    client = _client(data_dir)
    name = _collection_name_for_model(model_name)
    return client.get_or_create_collection(name)


def delete_by_source_id(
    data_dir: Path | None,
    source_id: int | str,
    embedding_model: str | None,
) -> None:
    """删除某 source 的向量；embedding_model 为空时仅清理旧版集合。"""
    sid = str(source_id)
    client = _client(data_dir)
    if embedding_model and embedding_model.strip():
        name = _collection_name_for_model(embedding_model.strip())
        try:
            coll = client.get_collection(name)
        except Exception:
            coll = None
        if coll is not None:
            coll.delete(where={"source_id": sid})
    try:
        leg = client.get_collection(LEGACY_COLLECTION_NAME)
        leg.delete(where={"source_id": sid})
    except Exception:
        pass


def add_interview_chunks(
    data_dir: Path | None,
    *,
    texts: list[str],
    embeddings: list[list[float]],
    source_type: str,
    source_id: int | str,
    model_name: str,
) -> None:
    if len(texts) != len(embeddings):
        raise ValueError("texts and embeddings length mismatch")
    coll = get_collection(data_dir, model_name)
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
    model_name: str,
    where: dict | None = None,
) -> dict:
    coll = get_collection(data_dir, model_name)
    return coll.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
