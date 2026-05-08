from types import SimpleNamespace


async def fake_fetch_ok(url: str, retain_html: bool = False):
    text = "薪资：30-40万/年\n" + "x" * 480
    html = f"<html><title>Java工程师-测试科技-BOSS</title><body><article>{text}</article></body></html>"
    return SimpleNamespace(
        ok=True,
        title="Java工程师-测试科技-BOSS",
        text=text,
        error=None,
        raw_html=html if retain_html else None,
    )


def test_create_job_from_url_and_pipeline(client, monkeypatch):
    monkeypatch.setattr("app.services.fetch_html.fetch_and_extract", fake_fetch_ok)

    r = client.post(
        "/api/jobs/",
        json={"jd_source_url": "https://example.com/job/1"},
    )
    assert r.status_code == 200
    job = r.json()
    assert job["jd_fetch_status"] == "ok"
    assert job["company"] == "测试科技"
    assert "工程师" in job["title"]
    assert job["salary"] != ""
    jid = job["id"]

    r2 = client.put(f"/api/jobs/{jid}/pipeline", json={"stages": ["笔试", "一面"]})
    assert r2.status_code == 200
    assert r2.json()["current_stage_id"] is not None

    first_stage_id = r2.json()["current_stage_id"]

    r4 = client.patch(f"/api/jobs/{jid}", json={"current_stage_id": first_stage_id})
    assert r4.status_code == 200


def test_create_job_requires_valid_url(client):
    r = client.post("/api/jobs/", json={"jd_source_url": "ftp://bad"})
    assert r.status_code == 422


def test_patch_job_manual_fields(client, monkeypatch):
    monkeypatch.setattr("app.services.fetch_html.fetch_and_extract", fake_fetch_ok)

    jid = client.post(
        "/api/jobs/",
        json={"jd_source_url": "https://example.com/job/patch"},
    ).json()["id"]

    r = client.patch(
        f"/api/jobs/{jid}",
        json={
            "company": "手填公司",
            "title": "手填职位",
            "salary": "40k",
            "published_at": "2024-06-01T00:00:00",
            "jd_source_url": "https://example.com/other-job",
            "jd_fetch_status": "failed",
            "jd_text": "手工粘贴的 JD 全文",
        },
    )
    assert r.status_code == 200
    o = r.json()
    assert o["company"] == "手填公司"
    assert o["title"] == "手填职位"
    assert o["salary"] == "40k"
    assert o["jd_fetch_status"] == "failed"
    assert "手工粘贴" in o["jd_text"]
    assert o["jd_source_url"] == "https://example.com/other-job"


def test_put_pipeline_resets_invalid_stage(client, monkeypatch):
    monkeypatch.setattr("app.services.fetch_html.fetch_and_extract", fake_fetch_ok)

    j = client.post(
        "/api/jobs/",
        json={"jd_source_url": "https://example.com/job/2"},
    ).json()
    jid = j["id"]

    client.put(f"/api/jobs/{jid}/pipeline", json={"stages": ["A", "B"]})
    client.put(f"/api/jobs/{jid}/pipeline", json={"stages": ["P"]})

    out = client.get(f"/api/jobs/{jid}").json()
    assert out["current_stage_id"] is not None
