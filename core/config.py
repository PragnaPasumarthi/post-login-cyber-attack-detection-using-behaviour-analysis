from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SENDGRID_API_KEY: str = "placeholder"   # Set in .env
    REDIS_URL: str = "redis://localhost:6379/0"
    MONGODB_URL: str = "mongodb://localhost:27017"
    JWT_SECRET: str = "super_secret_key"

    class Config:
        env_file = ".env"

settings = Settings()
