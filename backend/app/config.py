import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# ini penting supaya isi .env di-root folder terbaca
load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "Parking System"
    APP_VERSION: str = "1.0.0"

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "postgres")     # default postgres
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "788979") # default password sesuai .env
    DB_NAME: str = os.getenv("DB_NAME", "parking_system")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey12345")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
