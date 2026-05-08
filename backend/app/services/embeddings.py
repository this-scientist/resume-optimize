from __future__ import annotations

import threading
from typing import Any

from FlagEmbedding import FlagModel

ZH_QUERY_INSTRUCTION_FOR_RETRIEVAL = "为这个句子生成表示以用于检索相关文章："
EN_QUERY_INSTRUCTION_FOR_RETRIEVAL = "Represent this sentence for searching relevant passages: "

_MODEL_LOCK = threading.Lock()
_MODEL_CACHE: dict[str, FlagModel] = {}


def _query_instruction_for_model(model_name: str) -> str:
    lower = model_name.lower()
    if "zh" in lower or "chinese" in lower:
        return ZH_QUERY_INSTRUCTION_FOR_RETRIEVAL
    return EN_QUERY_INSTRUCTION_FOR_RETRIEVAL


def _cache_key(model_name: str, *, use_fp16: bool, query_instruction: str) -> str:
    return f"{model_name}\0{use_fp16}\0{query_instruction}"


def get_flag_model(
    model_name: str,
    *,
    use_fp16: bool = True,
    query_instruction: str | None = None,
) -> FlagModel:
    """Lazy-load FlagEmbedding model (singleton per model_name + options)."""
    qi = query_instruction if query_instruction is not None else _query_instruction_for_model(model_name)
    key = _cache_key(model_name, use_fp16=use_fp16, query_instruction=qi)
    with _MODEL_LOCK:
        if key not in _MODEL_CACHE:
            _MODEL_CACHE[key] = FlagModel(
                model_name,
                use_fp16=use_fp16,
                query_instruction_for_retrieval=qi,
            )
        return _MODEL_CACHE[key]


def _vectors_to_nested_lists(arr: Any) -> list[list[float]]:
    import numpy as np

    try:
        import torch
    except ImportError:
        torch = None  # type: ignore[assignment]

    if torch is not None and isinstance(arr, torch.Tensor):
        arr = arr.detach().cpu().numpy()
    if isinstance(arr, np.ndarray):
        return arr.astype("float64").tolist()
    raise TypeError(f"unexpected embedding array type: {type(arr)}")


def embed_corpus(
    texts: list[str],
    *,
    model: str,
    batch_size: int = 32,
    use_fp16: bool = True,
) -> list[list[float]]:
    """Encode passages / document chunks for indexing (no query instruction)."""
    if not texts:
        return []
    m = get_flag_model(model, use_fp16=use_fp16)
    raw = m.encode_corpus(texts, batch_size=batch_size)
    return _vectors_to_nested_lists(raw)


def embed_queries(
    texts: list[str],
    *,
    model: str,
    batch_size: int = 32,
    use_fp16: bool = True,
) -> list[list[float]]:
    """Encode retrieval queries (uses query_instruction_for_retrieval)."""
    if not texts:
        return []
    m = get_flag_model(model, use_fp16=use_fp16)
    raw = m.encode_queries(texts, batch_size=batch_size)
    return _vectors_to_nested_lists(raw)
