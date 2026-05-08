from app.db import models
from app.db.session import session_scope


def test_resume_crud(client):
    r = client.post(
        "/api/resumes/",
        json={"title": "T1", "category": "互联网", "current_body_md": "# v1"},
    )
    assert r.status_code == 200
    rid = r.json()["id"]

    assert client.get(f"/api/resumes/{rid}").status_code == 200
    client.patch(f"/api/resumes/{rid}", json={"current_body_md": "# v2"})
    assert client.get(f"/api/resumes/{rid}").json()["current_body_md"] == "# v2"

    r_del = client.delete(f"/api/resumes/{rid}")
    assert r_del.status_code == 204
    assert client.get(f"/api/resumes/{rid}").status_code == 404


def test_resume_list(client):
    client.post("/api/resumes/", json={"title": "a"})
    r = client.get("/api/resumes/")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_restore_revision(client):
    r = client.post("/api/resumes/", json={"title": "T", "current_body_md": "# now"})
    rid = r.json()["id"]

    with session_scope() as db:
        rev = models.ResumeRevision(resume_id=rid, body_md="# old", source="user_edit")
        db.add(rev)
        db.flush()
        rev_id = rev.id

    r2 = client.post(f"/api/resumes/{rid}/revisions/{rev_id}/restore")
    assert r2.status_code == 200
    assert r2.json()["current_body_md"] == "# old"
