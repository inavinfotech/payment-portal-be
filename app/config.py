import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Payment Service")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "1.0.0")

    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET")
    
    ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY")

settings = Settings()
