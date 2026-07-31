from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql://wealth_user:wealth_password@localhost:5432/wealth_mvp"
    )

    class Config:
        env_file = ".env"


settings = Settings()