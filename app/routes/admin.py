from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..auth import get_current_admin
from .. import schemas, models

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_admin)]
)

@router.get("/apps", response_model=List[schemas.AppResponse])
async def get_apps(db: Session = Depends(get_db)):
    return db.query(models.App).all()

@router.post("/apps", response_model=schemas.AppCreateResponse)
async def create_app(app: schemas.AppCreate, db: Session = Depends(get_db)):
    import uuid
    import secrets
    from ..auth import get_password_hash
    
    api_key = f"app_{secrets.token_urlsafe(16)}"
    api_secret = secrets.token_urlsafe(32)
    
    db_app = models.App(
        name=app.name,
        api_key=api_key,
        api_secret_hash=get_password_hash(api_secret)
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    
    return schemas.AppCreateResponse(
        id=db_app.id,
        name=db_app.name,
        api_key=api_key,
        api_secret=api_secret,
        created_at=db_app.created_at
    )

@router.get("/payments", response_model=List[schemas.PaymentResponse])
async def get_payments(
    app_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Payment, models.App.name.label("app_name"))\
        .join(models.App, models.Payment.app_id == models.App.id)
    
    if app_id:
        query = query.filter(models.Payment.app_id == app_id)
    if status:
        query = query.filter(models.Payment.status == status)
        
    results = query.all()
    
    # Map results to schema
    return [
        {**payment.__dict__, "app_name": app_name} 
        for payment, app_name in results
    ]

@router.get("/dashboard-summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    total_payments = db.query(models.Payment).count()
    total_revenue = db.query(func.sum(models.Payment.amount)).filter(models.Payment.status == "paid").scalar() or 0
    
    # Revenue by app
    revenue_by_app = db.query(
        models.Payment.app_id, 
        func.sum(models.Payment.amount).label("total")
    ).filter(models.Payment.status == "paid").group_by(models.Payment.app_id).all()
    
    return {
        "total_payments": total_payments,
        "total_revenue": total_revenue,
        "revenue_by_app": [{"app_id": r[0], "total": r[1]} for r in revenue_by_app]
    }
