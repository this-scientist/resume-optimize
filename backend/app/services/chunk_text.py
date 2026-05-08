from __future__ import annotations

DEFAULT_MAX_CHARS = 900
DEFAULT_OVERLAP = 80


def chunk_text(
    s: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """
    将全文按段落边界保留在字符串中，再以滑动窗口切分为多块（块最大 max_chars，相邻块重叠 overlap）。
    """
    if overlap >= max_chars:
        raise ValueError("overlap must be less than max_chars")
    if not s:
        return []

    chunks: list[str] = []
    n = len(s)
    i = 0
    while i < n:
        end = min(i + max_chars, n)
        chunks.append(s[i:end])
        if end >= n:
            break
        i += max_chars - overlap
    return chunks
