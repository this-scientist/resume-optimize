from __future__ import annotations

from pydantic import BaseModel, Field


class SettingsPayload(BaseModel):
    chat_base_url: str = ""
    chat_api_key: str = ""
    chat_model: str = ""
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""


class SettingsRead(BaseModel):
    chat_base_url: str = ""
    chat_api_key: str = ""
    chat_model: str = ""
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
