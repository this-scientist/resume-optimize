from pathlib import Path

from app.db.session import make_engine
from app.services.paths import get_data_dir


def test_data_dir_respects_env(tmp_path, monkeypatch):
    monkeypatch.setenv("RESUME_OPTIMIZER_DATA_DIR", str(tmp_path))
    d = get_data_dir()
    assert d == tmp_path.resolve()
    assert d.is_dir()


def test_make_engine_creates_sqlite_file(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    url = f"sqlite:///{db_path.as_posix()}"
    engine = make_engine(url)
    engine.dispose()
    assert db_path.exists()


def test_sqlite_url_helper(tmp_path):
    from app.services.paths import sqlite_url

    u = sqlite_url(Path(tmp_path))
    assert u.startswith("sqlite:///")
    assert "app.sqlite3" in u
