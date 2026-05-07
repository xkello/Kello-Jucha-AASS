from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Timesheet & Absence Portal"
    app_env: str = "development"
    secret_key: str = "super-secret-change-me"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/timesheet_portal"
    seed_demo_data: bool = True
    demo_password: str = "demo123"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
