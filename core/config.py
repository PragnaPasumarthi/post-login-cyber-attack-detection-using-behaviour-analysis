from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Gmail SMTP credentials (use an App Password from myaccount.google.com/apppasswords)
    SMTP_EMAIL: str = "placeholder"
    SMTP_APP_PASSWORD: str = "placeholder"
    REDIS_URL: str = "redis://localhost:6379/0"
    MONGO_URI: str = "placeholder"  # Set in .env (MongoDB Atlas connection string)
    JWT_SECRET: str = "super_secret_key"

    class Config:
        env_file = ".env"

settings = Settings()
