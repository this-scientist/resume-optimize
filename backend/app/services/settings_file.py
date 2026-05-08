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


def save_settings_json(data: dict) -> None:
    path = settings_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]
