from __future__ import annotations


def clip_chunks(chunks: list[str], max_chars: int) -> str:
    """
    将已按相关度降序排列的片段依次拼接，总长度不超过 max_chars；最后一个片段可能被截断。
    """
    if max_chars <= 0:
        return ""

    parts: list[str] = []
    used = 0
    for chunk in chunks:
        if used >= max_chars:
            break
        remaining = max_chars - used
        if len(chunk) <= remaining:
            parts.append(chunk)
            used += len(chunk)
        else:
            parts.append(chunk[:remaining])
            break
    return "".join(parts)
