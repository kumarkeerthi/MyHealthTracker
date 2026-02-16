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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
