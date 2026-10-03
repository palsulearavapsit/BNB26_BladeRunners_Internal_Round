from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SATYA"
    environment: str = "development"
    api_prefix: str = "/api"
    max_upload_bytes: int = 25 * 1024 * 1024
    supabase_url: str | None = None
    supabase_key: str | None = None
    persistence_mode: str = "supabase"
    local_fallback_enabled: bool = False
    whisper_api_key: str | None = None
    whisper_api_url: str = "https://api.openai.com/v1/audio/transcriptions"
    llm_provider: str = "gemini"
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SATYA_", extra="ignore")

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
