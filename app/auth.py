from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from . import models
from .config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_app(
    x_app_key: str = Header(..., alias="x-app-key", description="App API Key"),
    x_app_secret: str = Header(..., alias="x-app-secret", description="App API Secret"),
    db: Session = Depends(get_db)
):
    app = db.query(models.App).filter(models.App.api_key == x_app_key).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
        )
    if not verify_password(x_app_secret, app.api_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
        )
    return app

def get_current_admin(
    x_admin_key: str = Header(..., alias="x-admin-key", description="Admin API Key")
):
    import secrets
    if not secrets.compare_digest(x_admin_key, settings.ADMIN_SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin Credentials",
        )
    return True
