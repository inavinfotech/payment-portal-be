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

@router.get("/payments/export")
async def export_payments(
    format: str,
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
    
    # Convert to list of dicts
    data = []
    for payment, app_name in results:
        data.append({
            "App Name": app_name,
            "Razorpay Order ID": payment.razorpay_order_id,
            "Razorpay Payment ID": payment.razorpay_payment_id,
            "Amount": payment.amount,
            "Currency": payment.currency,
            "Status": payment.status,
            "Date": payment.created_at.strftime("%Y-%m-%d %H:%M:%S") if payment.created_at else "",
            "Paid At": payment.paid_at.strftime("%Y-%m-%d %H:%M:%S") if payment.paid_at else "",
            "Failure Reason": payment.metadata_info.get("failure_reason", "") if payment.metadata_info else ""
        })
        
    if not data:
         # Exporting empty file with headers is fine
         pass
         
    from ..services import export_service
    from fastapi.responses import StreamingResponse
    
    if format == "csv":
        file_stream = export_service.export_to_csv(data)
        filename = "payments.csv"
        media_type = "text/csv"
    elif format == "excel":
        file_stream = export_service.export_to_excel(data)
        filename = "payments.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif format == "pdf":
        file_stream = export_service.export_to_pdf(data)
        filename = "payments.pdf"
        media_type = "application/pdf"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
        
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    return StreamingResponse(iter([file_stream.getvalue()]), media_type=media_type, headers=headers)


@router.get("/dashboard-summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    total_payments = db.query(models.Payment).count()
    total_revenue = db.query(func.sum(models.Payment.amount)).filter(models.Payment.status == "paid").scalar() or 0
    
    # Revenue by app
    revenue_by_app = db.query(
        models.Payment.app_id, 
        func.sum(models.Payment.amount).label("total")
    ).filter(models.Payment.status == "paid").group_by(models.Payment.app_id).all()
    
    # Payment status counts
    status_counts = db.query(
        models.Payment.status,
        func.count(models.Payment.id).label("count")
    ).group_by(models.Payment.status).all()
    
    return {
        "total_payments": total_payments,
        "total_revenue": total_revenue,
        "revenue_by_app": [{"app_id": r[0], "total": r[1]} for r in revenue_by_app],
        "payment_status_counts": [{"status": r[0], "count": r[1]} for r in status_counts]
    }

# Settings Endpoints

@router.get("/settings")
async def get_settings(db: Session = Depends(get_db)):
    settings = db.query(models.SystemSetting).all()
    # Convert list of models to dict
    settings_dict = {s.key: s.value for s in settings}
    
    # Ensure default defaults exist in response if not in DB
    if "global_payment_enabled" not in settings_dict:
        settings_dict["global_payment_enabled"] = "true"
        
    return settings_dict

@router.post("/settings")
async def update_settings(settings: dict, db: Session = Depends(get_db)):
    for key, value in settings.items():
        setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            new_setting = models.SystemSetting(key=key, value=str(value))
            db.add(new_setting)
    
    db.commit()
    return {"status": "success", "message": "Settings updated"}

@router.put("/apps/{app_id}/status")
async def update_app_status(
    app_id: str, 
    status_update: schemas.AppStatusUpdate, 
    db: Session = Depends(get_db)
):
    app = db.query(models.App).filter(models.App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    app.is_active = status_update.is_active
    db.commit()
    return {"status": "success", "is_active": app.is_active}

@router.put("/apps/{app_id}/domains")
async def update_app_domains(
    app_id: str, 
    domains_update: schemas.AppDomainsUpdate, 
    db: Session = Depends(get_db)
):
    app = db.query(models.App).filter(models.App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    app.allowed_domains = domains_update.allowed_domains
    db.commit()
    return {"status": "success", "allowed_domains": app.allowed_domains}
