from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql://wealth_user:wealth_password@localhost:5432/wealth_mvp"
    )
    SECRET_KEY: str = "your-secret-key-change-in-production"

    class Config:
        env_file = ".env"


settings = Settings()