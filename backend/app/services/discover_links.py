from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DiscoveredLink:
    url: str
    label: str | None


async def fetch_html_document(url: str) -> tuple[str | None, str | None]:
    """返回 (html, error_message)。"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url)
    except Exception as exc:
        return None, str(exc)

    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"

    ct = (resp.headers.get("content-type") or "").lower()
    if "html" not in ct:
        return None, "Content-Type is not HTML"

    return resp.text, None


def extract_same_origin_links(
    html: str,
    base_url: str,
    *,
    max_links: int = 120,
) -> list[DiscoveredLink]:
    """
    从页面中提取与 base_url 同站的 http(s) 链接。
    优先 nav / aside / 目录区 / main 内的 <a>，再补充全页链接，去重保序。
    """
    base = urlparse(base_url)
    if base.scheme not in ("http", "https") or not base.netloc:
        return []

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    preferred_selectors = (
        "nav a[href]",
        "aside a[href]",
        '[role="navigation"] a[href]',
        ".sidebar a[href]",
        "#sidebar a[href]",
        ".toc a[href]",
        ".table-of-contents a[href]",
        "#table-of-contents a[href]",
        "article a[href]",
        "main a[href]",
    )

    seen: set[str] = set()
    out: list[DiscoveredLink] = []

    def push(abs_u: str, label: str | None) -> None:
        if len(out) >= max_links:
            return
        u, _ = urldefrag(abs_u)
        p = urlparse(u)
        if p.scheme not in ("http", "https"):
            return
        if p.netloc != base.netloc:
            return
        path_lower = (p.path or "").lower()
        skip_suffix = (".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js")
        if any(path_lower.endswith(s) for s in skip_suffix):
            return
        if u in seen:
            return
        seen.add(u)
        out.append(DiscoveredLink(url=u, label=(label or None)))

    for sel in preferred_selectors:
        for a in soup.select(sel):
            href = a.get("href")
            if not href or href.strip().startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            abs_u = urljoin(base_url, href)
            text = a.get_text(strip=True)
            push(abs_u, text[:500] if text else None)

    if len(out) < max_links:
        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href or href.strip().startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            abs_u = urljoin(base_url, href)
            text = a.get_text(strip=True)
            push(abs_u, text[:500] if text else None)

    return out


async def discover_links_for_url(url: str, *, max_links: int = 120) -> tuple[list[DiscoveredLink], str | None]:
    """
    抓取 url 对应 HTML 并提取同站链接。
    返回 (links, error)。links 首条可为当前页（若页面内未重复出现则会出现在列表中）。
    """
    html, err = await fetch_html_document(url)
    if err or not html:
        return [], err or "empty html"

    base_norm, _ = urldefrag(url)
    found = extract_same_origin_links(html, base_norm, max_links=max_links + 10)

    idx = next((i for i, x in enumerate(found) if x.url == base_norm), None)
    if idx is None:
        found.insert(0, DiscoveredLink(url=base_norm, label="（入口页）"))
    elif idx > 0:
        entry = found.pop(idx)
        found.insert(0, entry)

    return found[:max_links], None
