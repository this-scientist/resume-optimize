from types import SimpleNamespace


def test_create_manual_note_and_confirm_indexed(client, monkeypatch):
    monkeypatch.setenv("RESUME_OPTIMIZER_EMBEDDING_API_KEY", "sk-test")
    monkeypatch.setenv("RESUME_OPTIMIZER_EMBEDDING_MODEL", "text-embedding-3-small")

    class FakeEmbeddings:
        def create(self, model, input):
            class Item:
                def __init__(self, i):
                    self.embedding = [float(i), 0.1, 0.2]

            return SimpleNamespace(data=[Item(i) for i in range(len(input))])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.embeddings = FakeEmbeddings()

    monkeypatch.setattr("app.services.embeddings.OpenAI", FakeOpenAI)

    body = "段落一。\n\n" + ("面试记录内容。" * 80)
    r = client.post("/api/interview-sources", json={"note_text": body})
    assert r.status_code == 200
    data = r.json()
    assert data["fetch_status"] == "ok"
    assert data["index_status"] == "pending"
    sid = data["id"]

    r2 = client.post(f"/api/interview-sources/{sid}/confirm")
    assert r2.status_code == 200
    assert r2.json()["index_status"] == "indexed"


def test_create_from_url_mock_fetch(client, monkeypatch):
    long_html = "<p>" + ("你好世界" * 80) + "</p>"

    async def fake_fetch(url: str):
        return SimpleNamespace(
            ok=True,
            title="示例",
            text=long_html,
            error=None,
        )

    monkeypatch.setattr("app.services.fetch_html.fetch_and_extract", fake_fetch)

    r = client.post("/api/interview-sources", json={"url": "http://example.com/jd"})
    assert r.status_code == 200
    assert r.json()["fetch_status"] == "ok"
    assert "你好世界" in r.json()["body_preview"]


def test_delete_source_removes_row(client):
    r = client.post("/api/interview-sources", json={"note_text": "x" * 400})
    assert r.status_code == 200
    sid = r.json()["id"]

    r2 = client.delete(f"/api/interview-sources/{sid}")
    assert r2.status_code == 204

    r3 = client.delete(f"/api/interview-sources/{sid}")
    assert r3.status_code == 404
