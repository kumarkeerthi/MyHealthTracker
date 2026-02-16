from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Metabolic Intelligence Engine"
    database_url: str = Field(
        default="postgresql+psycopg2://metabolic:metabolic@db:5432/metabolic"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
