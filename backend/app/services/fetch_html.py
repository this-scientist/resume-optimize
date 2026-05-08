from __future__ import annotations

from dataclasses import dataclass

import httpx
import trafilatura
from trafilatura.metadata import extract_metadata

# 正文过短视为抓取/抽取失败（噪声页、反爬空白等）
MIN_EXTRACTED_TEXT_CHARS = 200


@dataclass
class FetchResult:
    ok: bool
    title: str | None
    text: str
    error: str | None = None
    raw_html: str | None = None


async def _get(url: str):
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        return await client.get(url)


async def fetch_and_extract(url: str, *, retain_html: bool = False) -> FetchResult:
    try:
        resp = await _get(url)
    except Exception as exc:
        return FetchResult(ok=False, title=None, text="", error=str(exc))

    if resp.status_code != 200:
        return FetchResult(
            ok=False,
            title=None,
            text="",
            error=f"HTTP {resp.status_code}",
        )

    content_type = (resp.headers.get("content-type") or "").lower()
    if "html" not in content_type:
        return FetchResult(ok=False, title=None, text="", error="Content-Type is not HTML")

    html = resp.text
    try:
        text = trafilatura.extract(html, url=url) or ""
        meta = extract_metadata(html, default_url=url)
        title = meta.title if meta else None
    except Exception as exc:
        return FetchResult(
            ok=False,
            title=None,
            text="",
            error=str(exc),
            raw_html=html if retain_html else None,
        )

    if len(text.strip()) < MIN_EXTRACTED_TEXT_CHARS:
        return FetchResult(
            ok=False,
            title=title,
            text=text,
            error=f"extracted text shorter than {MIN_EXTRACTED_TEXT_CHARS} characters",
            raw_html=html if retain_html else None,
        )

    return FetchResult(
        ok=True,
        title=title,
        text=text,
        error=None,
        raw_html=html if retain_html else None,
    )
