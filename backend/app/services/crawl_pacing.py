from __future__ import annotations

import random

from pydantic import BaseModel


class CrawlPacingParams(BaseModel):
    """批量抓取节奏：模拟「读完上一页的一半时间后再打开下一页」。"""

    chars_per_minute: float = 400.0
    min_delay_sec: float = 2.0
    max_delay_sec: float = 120.0
    jitter_ratio: float = 0.1


def gap_seconds_before_next_fetch(
    previous_page_char_count: int,
    params: CrawlPacingParams | None = None,
) -> float:
    """
    根据**上一页**正文字符数估算阅读时长，取一半作为进入下一页前的等待秒数。

    阅读时长 ≈ 字数 / 每分钟阅读字数（默认 400，偏中文浏览）；间隔 = 阅读时长 / 2。
    结果夹在 [min_delay_sec, max_delay_sec]，并可加轻微抖动弱化节律特征。
    """
    p = params or CrawlPacingParams()
    cpm = max(p.chars_per_minute, 1.0)

    if previous_page_char_count <= 0:
        base = p.min_delay_sec
    else:
        read_seconds = (previous_page_char_count / cpm) * 60.0
        base = read_seconds / 2.0

    base = max(p.min_delay_sec, min(p.max_delay_sec, base))

    if p.jitter_ratio and p.jitter_ratio > 0:
        jitter = 1.0 + random.uniform(-p.jitter_ratio, p.jitter_ratio)
        base *= jitter
        base = max(p.min_delay_sec, min(p.max_delay_sec, base))

    return float(base)
