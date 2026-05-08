from app.services.optimize_resume import build_optimize_user_message


def test_build_optimize_user_message_includes_sections():
    msg = build_optimize_user_message(
        jd_text="需要后端",
        retrieved_context="问了 Redis",
        resume_md="# Me",
        extra_instructions="突出 Go",
    )
    assert "需要后端" in msg
    assert "Redis" in msg
    assert "突出 Go" in msg


def test_optimize_endpoint_mocked(client, monkeypatch):
    monkeypatch.setenv("RESUME_OPTIMIZER_EMBEDDING_API_KEY", "ek")
    monkeypatch.setenv("RESUME_OPTIMIZER_EMBEDDING_MODEL", "em")
    monkeypatch.setenv("RESUME_OPTIMIZER_CHAT_API_KEY", "ck")
    monkeypatch.setenv("RESUME_OPTIMIZER_CHAT_MODEL", "cm")

    rid = client.post("/api/resumes/", json={"current_body_md": "# Me"}).json()["id"]
    jid = client.post("/api/jobs/", json={"company": "c"}).json()["id"]
    client.patch(f"/api/jobs/{jid}", json={"jd_text": "岗位职责..." * 50})

    monkeypatch.setattr(
        "app.services.optimize_resume.embed_chunks",
        lambda texts, **kw: [[0.1, 0.2, 0.3] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.optimize_resume.chroma_store.query_by_embedding",
        lambda *a, **k: {"documents": [["检索片段A", "检索片段B"]]},
    )
    monkeypatch.setattr(
        "app.services.optimize_resume.complete_chat",
        lambda **kw: "# 优化后的简历\n\n- 技能",
    )

    r = client.post(f"/api/resumes/{rid}/optimize", json={"job_id": jid, "top_k": 4})
    assert r.status_code == 200
    assert r.json()["revision_id"] >= 1

    body = client.get(f"/api/resumes/{rid}").json()["current_body_md"]
    assert "优化后的简历" in body
