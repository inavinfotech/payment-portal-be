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
    
    # Seed data
    # from .services.seeding import seed_data
    # seed_data()
    
    yield
    
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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
