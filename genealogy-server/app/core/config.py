from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "genealogy-server"
    app_env: str = "dev"

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    upload_dir: str = "uploads"

    # Portal display family; unset = auto-pick family with most persons
    display_family_id: int | None = None
    # future: set True to require login on /api/public/*
    public_require_auth: bool = False

    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
