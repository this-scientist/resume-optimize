from __future__ import annotations

from openai import OpenAI


def embed_chunks(
    texts: list[str],
    *,
    api_key: str,
    base_url: str | None,
    model: str,
    batch_size: int = 16,
) -> list[list[float]]:
    if not texts:
        return []
    client = OpenAI(api_key=api_key, base_url=base_url or None)
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        out.extend(item.embedding for item in resp.data)
    return out
