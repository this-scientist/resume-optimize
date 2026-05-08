from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedJobFields:
    company: str = ""
    job_title: str = ""
    salary: str = ""
    published_at: datetime | None = None


_SITE_HINTS = (
    "BOSS",
    "智联",
    "前程",
    "猎聘",
    "拉勾",
    "实习僧",
    "招聘网",
    "官网",
    "拉勾网",
    "脉脉",
)


def _is_site_noise(segment: str) -> bool:
    s = segment.strip()
    if len(s) <= 1:
        return True
    return any(h in s for h in _SITE_HINTS)


def split_title_meta(page_title: str | None) -> tuple[str, str]:
    """从浏览器标题解析 (company, job_title)。常见：职位 - 公司 - 平台。"""
    if not page_title:
        return "", ""
    parts = [
        p.strip()
        for p in re.split(r"\s*[-–—|丨]\s*", page_title.strip())
        if p.strip()
    ]
    if not parts:
        return "", ""
    filtered = [p for p in parts if not _is_site_noise(p)]
    seg = filtered if len(filtered) >= 2 else parts
    if len(seg) >= 2:
        job_title = seg[0][:255]
        company = seg[1][:255]
        return company, job_title
    return "", seg[0][:255]


def extract_salary(text: str) -> str:
    if not text:
        return ""
    head = text[:8000]
    if re.search(r"面议", head):
        return "面议"
    patterns = [
        r"(\d+(?:\.\d+)?\s*[-–至]\s*\d+(?:\.\d+)?\s*万(?:元)?(?:/\s*年)?)",
        r"(\d+(?:\.\d+)?万\s*/\s*年)",
        r"(\d+[kK]\s*[-–]\s*\d+[kK](?:\s*/\s*月)?)",
        r"(?:薪资|薪水|薪酬|工资)[：:\s]*([^\n\r]{1,48})",
    ]
    for pat in patterns:
        m = re.search(pat, head, re.I)
        if m:
            return (m.group(1) if m.lastindex else m.group(0)).strip()[:128]
    return ""


def extract_published_at(html: str, text: str) -> datetime | None:
    blob = (html or "")[:60000] + "\n" + (text or "")[:8000]
    tries = [
        r"发布(?:时间|于)?[：:\s]*(\d{4})[-/](\d{1,2})[-/](\d{1,2})",
        r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})",
        r"(\d{4})年(\d{1,2})月(\d{1,2})日?",
        r'published[^"\']*content=["\'](\d{4}-\d{2}-\d{2})',
    ]
    for pat in tries:
        m = re.search(pat, blob)
        if not m:
            continue
        try:
            if len(m.groups()) == 3:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            elif len(m.groups()) == 1 and "-" in m.group(1):
                parts = m.group(1).split("-")
                y, mo, d = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                continue
            if 1990 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
                return datetime(y, mo, d)
        except (ValueError, IndexError, AttributeError):
            continue
    return None


def parse_job_fields(html: str, plain_text: str, page_title: str | None) -> ParsedJobFields:
    company, job_title = split_title_meta(page_title)
    if not job_title and page_title:
        job_title = page_title.strip()[:255]
    salary = extract_salary(plain_text)
    published_at = extract_published_at(html, plain_text)
    return ParsedJobFields(
        company=company[:255],
        job_title=job_title[:255],
        salary=salary[:128],
        published_at=published_at,
    )
