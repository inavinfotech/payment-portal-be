from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Payment Service"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    
    RAZORPAY_LIVE_KEY_ID: Optional[str] = None
    RAZORPAY_LIVE_KEY_SECRET: Optional[str] = None
    
    ADMIN_SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = ["*"] # BFF only
    FORCE_MOCK_PAYMENTS: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
