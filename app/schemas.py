from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class AppBase(BaseModel):
    name: str

class AppCreate(AppBase):
    is_live_mode: bool = False

class AppResponse(AppBase):
    id: str
    api_key: str
    api_secret_hash: str
    created_at: datetime
    is_active: bool
    is_live_mode: bool
    allowed_domains: str

    class Config:
        from_attributes = True

class AppCreateResponse(AppBase):
    id: str
    api_key: str
    api_secret: str
    created_at: datetime

# Payment Schemas
class PaymentCreate(BaseModel):
    user_id: str
    amount: int
    currency: str = "INR"
    plan_type: Optional[str] = None
    metadata_info: Optional[dict[str, Any]] = None

class PaymentResponse(BaseModel):
    id: str
    razorpay_order_id: Optional[str] = None
    amount: int
    currency: str
    status: str
    created_at: datetime
    app_name: Optional[str] = None
    metadata_info: Optional[dict[str, Any]] = None
    razorpay_payment_id: Optional[str] = None
    key_id: Optional[str] = None # For frontend use
    
    class Config:
        from_attributes = True

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentFail(BaseModel):
    razorpay_order_id: str
    reason: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

class PaymentCancel(BaseModel):
    razorpay_order_id: str
    reason: str

class AppStatusUpdate(BaseModel):
    is_active: bool

class AppModeUpdate(BaseModel):
    is_live_mode: bool

class AppDomainsUpdate(BaseModel):
    allowed_domains: str

class PaymentVerificationData(BaseModel):
    verification_status: str
    payment_id: str
    order_id: str
    amount_paid: int
    currency: str
    paid_at: Optional[datetime] = None
    method: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

class PaymentVerificationResponse(BaseModel):
    success: bool
    data: Optional[PaymentVerificationData] = None
    message: Optional[str] = None

# Auth Schemas
class LoginRequest(BaseModel):
    secret_key: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
