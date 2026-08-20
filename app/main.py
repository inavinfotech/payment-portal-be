from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import payments, admin, auth_routes
from .config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from .services.cleanup_service import process_stale_payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enable background scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_stale_payments, 'interval', minutes=5)
    scheduler.start()
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed default Razorpay account from .env if none exists
    _seed_default_razorpay_account()
    
    yield
    
    scheduler.shutdown()

def _seed_default_razorpay_account():
    """Seed a default RazorpayAccount from .env keys if no accounts exist yet."""
    from .database import SessionLocal
    from .encryption import encrypt_value
    from sqlalchemy.exc import IntegrityError
    
    db = SessionLocal()
    try:
        existing = db.query(models.RazorpayAccount).first()
        if existing:
            return  # Already has accounts, skip seeding
        
        # Only seed if .env keys are present
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return
        
        default_account = models.RazorpayAccount(
            id="default",
            name="Default Account",
            test_key_id=settings.RAZORPAY_KEY_ID,
            test_key_secret_enc=encrypt_value(settings.RAZORPAY_KEY_SECRET),
            live_key_id=settings.RAZORPAY_LIVE_KEY_ID,
            live_key_secret_enc=encrypt_value(settings.RAZORPAY_LIVE_KEY_SECRET) if settings.RAZORPAY_LIVE_KEY_SECRET else None,
            is_default=True
        )
        db.add(default_account)
        db.commit()
        db.refresh(default_account)
        
        # Link all existing orphan apps to the default account
        orphan_apps = db.query(models.App).filter(models.App.razorpay_account_id == None).all()
        for app in orphan_apps:
            app.razorpay_account_id = default_account.id
        db.commit()
        
        print(f"[SEED] Created default Razorpay account and linked {len(orphan_apps)} app(s)")
    except IntegrityError:
        db.rollback()
        print("[SEED] Default Razorpay account was already seeded by another process")
    except Exception as e:
        print(f"[SEED] Error seeding default Razorpay account: {e}")
        db.rollback()
    finally:
        db.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# Set up CORS
origins = [o for o in settings.ALLOWED_ORIGINS if o != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(auth_routes.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to Centralized Payment Service API"}

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8004, reload=True)
