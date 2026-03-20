from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TVU TikTok Analytics"
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    cors_origins_raw: str = "http://localhost:8501,http://127.0.0.1:8501"

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    hf_api_token: str = ""
    hf_model_id: str = "LeTuanKhaTTD/phobert-tvu-sentiment"

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins_raw.split(",") if x.strip()]


settings = Settings()
