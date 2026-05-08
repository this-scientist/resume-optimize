from __future__ import annotations

import json

from app.services.paths import get_data_dir


def settings_json_path():
    return get_data_dir() / "settings.json"


def load_settings_json() -> dict:
    path = settings_json_path()
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
