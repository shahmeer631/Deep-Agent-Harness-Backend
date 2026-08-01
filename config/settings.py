from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    agent_api_key: str = ""
    # "*" allows all browser origins (safe here: no cookie auth on the agent API)
    cors_origins: str = "*"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def cors_origin_list(self) -> list[str]:
        origins: list[str] = []
        for origin in self.cors_origins.split(","):
            cleaned = origin.strip().strip("\"'").rstrip("/")
            if cleaned:
                origins.append(cleaned)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
