import uuid
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime
import pytz

def get_ist_time():
    return datetime.now(pytz.timezone('Asia/Kolkata'))

class App(Base):
    __tablename__ = "apps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)
    api_secret_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_ist_time)
    is_active = Column(Boolean, default=True)
    is_live_mode = Column(Boolean, default=False)
    allowed_domains = Column(String, default="*") # Comma-separated list of allowed domains

    payments = relationship("Payment", back_populates="app")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True)
    value = Column(String)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String, ForeignKey("apps.id"), nullable=False)
    user_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False) # In smallest currency unit (e.g., paise)
    currency = Column(String, default="INR")
    plan_type = Column(String, nullable=True) # monthly/fixed
    razorpay_order_id = Column(String, unique=True, index=True)
    razorpay_payment_id = Column(String, nullable=True)
    status = Column(String, default="created") # created, paid, failed
    metadata_info = Column(JSON, nullable=True) # Renamed from metadata to avoid conflict with SQLAlchemy metadata
    created_at = Column(DateTime(timezone=True), default=get_ist_time)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    app = relationship("App", back_populates="payments")
