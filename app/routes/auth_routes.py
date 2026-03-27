from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
from .. import schemas, auth
from ..config import settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login", response_model=schemas.Token)
async def login(login_data: schemas.LoginRequest):
    if not secrets.compare_digest(login_data.secret_key, settings.ADMIN_SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin Secret Key",
        )
    
    access_token = auth.create_access_token(data={"sub": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify")
async def verify_token(is_valid: bool = Depends(auth.get_current_admin_user)):
    return {"status": "valid"}
