import pytest

from app.services import fetch_html


@pytest.mark.asyncio
async def test_fetch_extract_title_and_text(monkeypatch):
    long_body = "<p>" + ("你好世界" * 40) + "</p>"

    async def fake_get(url: str):
        class Resp:
            status_code = 200
            headers = {"content-type": "text/html; charset=utf-8"}
            text = f"<html><head><title>示例标题</title></head><body><article>{long_body}</article></body></html>"

        return Resp()

    monkeypatch.setattr(fetch_html, "_get", fake_get)
    out = await fetch_html.fetch_and_extract("http://example.com/x")
    assert "你好世界" in out.text
    assert out.ok is True
    assert out.error is None
    assert out.title == "示例标题"


@pytest.mark.asyncio
async def test_fetch_short_extract_is_not_ok(monkeypatch):
    async def fake_get(url: str):
        class Resp:
            status_code = 200
            headers = {"content-type": "text/html; charset=utf-8"}
            text = "<html><body><article><p>短</p></article></body></html>"

        return Resp()

    monkeypatch.setattr(fetch_html, "_get", fake_get)
    out = await fetch_html.fetch_and_extract("http://example.com/x")
    assert out.ok is False
    assert out.error is not None


@pytest.mark.asyncio
async def test_fetch_non_html_content_type(monkeypatch):
    async def fake_get(url: str):
        class Resp:
            status_code = 200
            headers = {"content-type": "application/json"}
            text = "{}"

        return Resp()

    monkeypatch.setattr(fetch_html, "_get", fake_get)
    out = await fetch_html.fetch_and_extract("http://example.com/x")
    assert out.ok is False
    assert out.error is not None
