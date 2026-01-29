from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://easm:easm@db:5432/easm"
    redis_url: str = "redis://redis:6380/0"

    class Config:
        env_file = ".env"
        env_prefix = "EASM_"


settings = Settings()
