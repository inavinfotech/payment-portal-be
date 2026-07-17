from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas, auth
from ..config import settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login", response_model=schemas.LoginResponse)
async def login(login_data: schemas.LoginRequest):
    if login_data.email != settings.DASHBOARD_EMAIL or login_data.password != settings.DASHBOARD_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Email or Password",
        )
    
    access_token = auth.create_access_token(data={"sub": settings.DASHBOARD_EMAIL, "role": "admin"})
    return {
        "status": "success",
        "email": settings.DASHBOARD_EMAIL,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/verify")
async def verify_token(is_valid: bool = Depends(auth.get_current_admin_user)):
    return {"status": "valid"}
