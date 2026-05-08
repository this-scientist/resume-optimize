from types import SimpleNamespace


async def fake_fetch_ok(url: str):
    return SimpleNamespace(ok=True, title="t", text="x" * 500, error=None)


def test_create_job_pipeline_and_patch_stage(client, monkeypatch):
    monkeypatch.setattr("app.services.fetch_html.fetch_and_extract", fake_fetch_ok)

    r = client.post(
        "/api/jobs/",
        json={"company": "A", "title": "B", "jd_source_url": "http://ex.com/x"},
    )
    assert r.status_code == 200
    job = r.json()
    assert job["jd_fetch_status"] == "ok"
    jid = job["id"]

    r2 = client.put(f"/api/jobs/{jid}/pipeline", json={"stages": ["笔试", "一面"]})
    assert r2.status_code == 200
    assert r2.json()["current_stage_id"] is not None

    first_stage_id = r2.json()["current_stage_id"]

    r4 = client.patch(f"/api/jobs/{jid}", json={"current_stage_id": first_stage_id})
    assert r4.status_code == 200


def test_put_pipeline_resets_invalid_stage(client):
    j = client.post("/api/jobs/", json={"company": "x", "title": "y"}).json()
    jid = j["id"]

    client.put(f"/api/jobs/{jid}/pipeline", json={"stages": ["A", "B"]})
    client.put(f"/api/jobs/{jid}/pipeline", json={"stages": ["P"]})

    out = client.get(f"/api/jobs/{jid}").json()
    assert out["current_stage_id"] is not None
