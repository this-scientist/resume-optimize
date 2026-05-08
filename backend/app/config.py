from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RESUME_OPTIMIZER_", env_file=".env", extra="ignore")
    host: str = "127.0.0.1"
    port: int = 8000
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    chat_base_url: str = ""
    chat_api_key: str = ""
    chat_model: str = ""


def get_settings() -> Settings:
    return Settings()
