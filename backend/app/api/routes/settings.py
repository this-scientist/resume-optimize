from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.settings import SettingsPayload, SettingsRead
from app.services.settings_file import load_settings_json, mask_secret, save_settings_json

router = APIRouter(prefix="/settings", tags=["settings"])


def _merge_defaults(settings: Settings, stored: dict) -> dict:
    return {
        "chat_base_url": stored.get("chat_base_url", settings.chat_base_url),
        "chat_api_key": stored.get("chat_api_key", settings.chat_api_key),
        "chat_model": stored.get("chat_model", settings.chat_model),
        "embedding_base_url": stored.get("embedding_base_url", settings.embedding_base_url),
        "embedding_api_key": stored.get("embedding_api_key", settings.embedding_api_key),
        "embedding_model": stored.get("embedding_model", settings.embedding_model),
    }


@router.get("/", response_model=SettingsRead)
def get_settings_payload(settings: Settings = Depends(get_settings)):
    stored = load_settings_json()
    merged = _merge_defaults(settings, stored)
    return SettingsRead(
        chat_base_url=merged["chat_base_url"],
        chat_api_key=mask_secret(merged["chat_api_key"]),
        chat_model=merged["chat_model"],
        embedding_base_url=merged["embedding_base_url"],
        embedding_api_key=mask_secret(merged["embedding_api_key"]),
        embedding_model=merged["embedding_model"],
    )


@router.put("/", response_model=SettingsRead)
def put_settings_payload(body: SettingsPayload, settings: Settings = Depends(get_settings)):
    data = body.model_dump()
    save_settings_json(data)
    merged = _merge_defaults(settings, data)
    return SettingsRead(
        chat_base_url=merged["chat_base_url"],
        chat_api_key=mask_secret(merged["chat_api_key"]),
        chat_model=merged["chat_model"],
        embedding_base_url=merged["embedding_base_url"],
        embedding_api_key=mask_secret(merged["embedding_api_key"]),
        embedding_model=merged["embedding_model"],
    )
