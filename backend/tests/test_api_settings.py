def test_settings_put_then_get_masked(client):
    r = client.put(
        "/api/settings/",
        json={
            "chat_base_url": "https://api.openai.com/v1",
            "chat_api_key": "sk-supersecretkey",
            "chat_model": "gpt-4",
            "embedding_base_url": "",
            "embedding_api_key": "emb-longsecret",
            "embedding_model": "text-embedding-3-small",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["chat_api_key"].startswith("****")
    assert data["chat_api_key"].endswith("tkey")
    assert data["embedding_api_key"].startswith("****")

    r2 = client.get("/api/settings/")
    assert r2.status_code == 200
    assert r2.json()["chat_model"] == "gpt-4"
