from __future__ import annotations

from app.config import Settings
from app.services.settings_file import load_settings_json


def effective_embedding_config(settings: Settings) -> tuple[str, str | None, str]:
    j = load_settings_json()
    api_key = (j.get("embedding_api_key") or "").strip() or settings.embedding_api_key
    base_raw = (j.get("embedding_base_url") or "").strip() or settings.embedding_base_url
    model = (j.get("embedding_model") or "").strip() or settings.embedding_model
    return api_key, (base_raw or None), model


def effective_chat_config(settings: Settings) -> tuple[str, str | None, str]:
    j = load_settings_json()
    api_key = (j.get("chat_api_key") or "").strip() or settings.chat_api_key
    base_raw = (j.get("chat_base_url") or "").strip() or settings.chat_base_url
    model = (j.get("chat_model") or "").strip() or settings.chat_model
    return api_key, (base_raw or None), model
