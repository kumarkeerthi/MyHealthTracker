from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Metabolic Intelligence Engine"
    database_url: str = Field(
        default="postgresql+psycopg2://metabolic:metabolic@db:5432/metabolic"
    )
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    llm_cache_ttl_seconds: int = 900
    max_food_image_bytes: int = 1_500_000
    food_image_upload_dir: str = "app/data/uploads"
    food_image_public_base_url: str = "https://s3.local/myhealthtracker/food-images"
    log_level: str = "INFO"
    log_dir: str = "logs"
    cors_allowed_origins: str = "https://app.example.com"
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    llm_requests_per_hour: int = 40
    jwt_secret: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    refresh_token_expiration_days: int = 7
    require_https: bool = True
    auth_bcrypt_rounds: int = 12
    login_rate_limit_attempts: int = 10
    login_rate_limit_window_seconds: int = 60
    admin_user_ids: str = "1"
    password_reset_token_ttl_minutes: int = 30
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@metabolicos.app"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
