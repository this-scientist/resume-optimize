import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RESUME_OPTIMIZER_DATA_DIR", str(tmp_path))
    from app.main import app

    return TestClient(app)
