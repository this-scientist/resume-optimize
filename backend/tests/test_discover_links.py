from app.services.discover_links import extract_same_origin_links


def test_extract_prefers_nav_and_same_origin():
    html = """
    <html><body>
    <nav><a href="/doc/a">第一章</a><a href="https://evil.com/x">外站</a></nav>
    <aside><a href="/doc/b">侧边</a></aside>
    <a href="mailto:x@y.com">mail</a>
    <a href="#frag">锚</a>
    <main><a href="/doc/c">正文链</a></main>
    </body></html>
    """
    base = "https://example.com/guide/start"
    links = extract_same_origin_links(html, base, max_links=50)
    urls = [x.url for x in links]
    assert "https://example.com/doc/a" in urls
    assert "https://example.com/doc/b" in urls
    assert "https://example.com/doc/c" in urls
    assert not any("evil.com" in u for u in urls)


def test_extract_skips_binary_suffix():
    html = '<a href="/x/report.pdf">pdf</a><a href="/y/z">ok</a>'
    links = extract_same_origin_links(html, "https://ex.com/", max_links=20)
    assert len(links) == 1
    assert links[0].url == "https://ex.com/y/z"
