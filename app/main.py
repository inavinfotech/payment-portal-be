from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import payments, admin
from .config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"],  # Expose all headers
)

app.include_router(payments.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Payment Service is running"}

# Background Scheduler for Cleanup
from apscheduler.schedulers.background import BackgroundScheduler
from .services.cleanup_service import process_stale_payments

scheduler = BackgroundScheduler()
# Run every 5 minutes
scheduler.add_job(process_stale_payments, 'interval', minutes=5)
scheduler.start()

# Shutdown scheduler on app exit
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
