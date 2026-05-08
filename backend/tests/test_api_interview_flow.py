from types import SimpleNamespace


def test_create_manual_note_and_confirm_indexed(client, monkeypatch):
    monkeypatch.setenv("RESUME_OPTIMIZER_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

    import numpy as np

    class FakeModel:
        def __init__(self, *a, **k):
            pass

        def encode_corpus(self, texts, batch_size=None, **kwargs):
            return np.array([[float(i), 0.1, 0.2] for i in range(len(texts))], dtype=np.float32)

    monkeypatch.setattr("app.services.embeddings.FlagModel", FakeModel)

    body = "段落一。\n\n" + ("面试记录内容。" * 80)
    r = client.post("/api/interview-sources/", json={"note_text": body})
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

    r = client.post("/api/interview-sources/", json={"url": "http://example.com/jd"})
    assert r.status_code == 200
    assert r.json()["fetch_status"] == "ok"
    assert "你好世界" in r.json()["body_preview"]


def test_list_and_get_interview_source_detail(client):
    r = client.post("/api/interview-sources/", json={"note_text": "hello detail"})
    assert r.status_code == 200
    sid = r.json()["id"]

    r_list = client.get("/api/interview-sources/")
    assert r_list.status_code == 200
    arr = r_list.json()
    assert len(arr) >= 1
    assert any(x["id"] == sid for x in arr)
    first = next(x for x in arr if x["id"] == sid)
    assert "created_at" in first
    assert first["body_preview"].startswith("hello")

    r_one = client.get(f"/api/interview-sources/{sid}")
    assert r_one.status_code == 200
    one = r_one.json()
    assert one["body_md"] == "hello detail"
    assert one["kind"] == "manual_note"


def test_delete_source_removes_row(client):
    r = client.post("/api/interview-sources/", json={"note_text": "x" * 400})
    assert r.status_code == 200
    sid = r.json()["id"]

    r2 = client.delete(f"/api/interview-sources/{sid}")
    assert r2.status_code == 204

    r3 = client.delete(f"/api/interview-sources/{sid}")
    assert r3.status_code == 404
