from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..auth import get_current_admin_user
from .. import schemas, models
from ..encryption import encrypt_value

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_admin_user)]
)

# ─── Razorpay Account Endpoints ─────────────────────────────────────────────

@router.get("/razorpay-accounts")
async def get_razorpay_accounts(db: Session = Depends(get_db)):
    accounts = db.query(models.RazorpayAccount).all()
    result = []
    for acc in accounts:
        app_count = db.query(models.App).filter(models.App.razorpay_account_id == acc.id).count()
        result.append({
            "id": acc.id,
            "name": acc.name,
            "test_key_id": acc.test_key_id,
            "has_live_keys": bool(acc.live_key_id and acc.live_key_secret_enc),
            "live_key_id": acc.live_key_id,
            "is_default": acc.is_default,
            "created_at": acc.created_at,
            "app_count": app_count
        })
    return result

@router.post("/razorpay-accounts")
async def create_razorpay_account(account: schemas.RazorpayAccountCreate, db: Session = Depends(get_db)):
    db_account = models.RazorpayAccount(
        name=account.name,
        test_key_id=account.test_key_id,
        test_key_secret_enc=encrypt_value(account.test_key_secret),
        live_key_id=account.live_key_id,
        live_key_secret_enc=encrypt_value(account.live_key_secret) if account.live_key_secret else None,
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return {
        "id": db_account.id,
        "name": db_account.name,
        "test_key_id": db_account.test_key_id,
        "has_live_keys": bool(db_account.live_key_id and db_account.live_key_secret_enc),
        "live_key_id": db_account.live_key_id,
        "is_default": db_account.is_default,
        "created_at": db_account.created_at,
        "app_count": 0
    }

@router.put("/razorpay-accounts/{account_id}")
async def update_razorpay_account(
    account_id: str,
    update: schemas.RazorpayAccountUpdate,
    db: Session = Depends(get_db)
):
    acc = db.query(models.RazorpayAccount).filter(models.RazorpayAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Razorpay account not found")

    if update.name is not None:
        acc.name = update.name
    if update.test_key_id is not None:
        acc.test_key_id = update.test_key_id
    if update.test_key_secret is not None:
        acc.test_key_secret_enc = encrypt_value(update.test_key_secret)
    if update.live_key_id is not None:
        acc.live_key_id = update.live_key_id
    if update.live_key_secret is not None:
        acc.live_key_secret_enc = encrypt_value(update.live_key_secret)

    db.commit()
    db.refresh(acc)
    app_count = db.query(models.App).filter(models.App.razorpay_account_id == acc.id).count()

    return {
        "id": acc.id,
        "name": acc.name,
        "test_key_id": acc.test_key_id,
        "has_live_keys": bool(acc.live_key_id and acc.live_key_secret_enc),
        "live_key_id": acc.live_key_id,
        "is_default": acc.is_default,
        "created_at": acc.created_at,
        "app_count": app_count
    }

@router.delete("/razorpay-accounts/{account_id}")
async def delete_razorpay_account(account_id: str, db: Session = Depends(get_db)):
    acc = db.query(models.RazorpayAccount).filter(models.RazorpayAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Razorpay account not found")

    if acc.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete the default account")

    linked_apps = db.query(models.App).filter(models.App.razorpay_account_id == account_id).count()
    if linked_apps > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete account with {linked_apps} linked app(s). Reassign them first."
        )

    db.delete(acc)
    db.commit()
    return {"status": "success", "message": "Razorpay account deleted"}

# ─── App Endpoints ───────────────────────────────────────────────────────────

@router.get("/apps")
async def get_apps(db: Session = Depends(get_db)):
    apps = db.query(models.App).all()
    result = []
    for app in apps:
        app_dict = {
            "id": app.id,
            "name": app.name,
            "api_key": app.api_key,
            "api_secret_hash": app.api_secret_hash,
            "created_at": app.created_at,
            "is_active": app.is_active,
            "is_live_mode": app.is_live_mode,
            "allowed_domains": app.allowed_domains,
            "razorpay_account_id": app.razorpay_account_id,
            "razorpay_account_name": app.razorpay_account.name if app.razorpay_account else None,
        }
        result.append(app_dict)
    return result

@router.post("/apps", response_model=schemas.AppCreateResponse)
async def create_app(app: schemas.AppCreate, db: Session = Depends(get_db)):
    import uuid
    import secrets
    from ..auth import get_password_hash
    
    api_key = f"app_{secrets.token_urlsafe(16)}"
    api_secret = secrets.token_urlsafe(32)

    # Validate razorpay_account_id if provided
    if app.razorpay_account_id:
        acc = db.query(models.RazorpayAccount).filter(
            models.RazorpayAccount.id == app.razorpay_account_id
        ).first()
        if not acc:
            raise HTTPException(status_code=400, detail="Invalid Razorpay account ID")
    else:
        # Assign default account if available
        default_acc = db.query(models.RazorpayAccount).filter(
            models.RazorpayAccount.is_default == True
        ).first()
        if default_acc:
            app.razorpay_account_id = default_acc.id
    
    db_app = models.App(
        name=app.name,
        api_key=api_key,
        api_secret_hash=get_password_hash(api_secret),
        is_live_mode=app.is_live_mode,
        razorpay_account_id=app.razorpay_account_id
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

@router.put("/apps/{app_id}/mode")
async def update_app_mode(
    app_id: str, 
    mode_update: schemas.AppModeUpdate, 
    db: Session = Depends(get_db)
):
    app = db.query(models.App).filter(models.App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    app.is_live_mode = mode_update.is_live_mode
    db.commit()
    return {"status": "success", "is_live_mode": app.is_live_mode}

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

@router.put("/apps/{app_id}/razorpay-account")
async def update_app_razorpay_account(
    app_id: str,
    account_update: schemas.AppAccountUpdate,
    db: Session = Depends(get_db)
):
    app = db.query(models.App).filter(models.App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    if account_update.razorpay_account_id:
        acc = db.query(models.RazorpayAccount).filter(
            models.RazorpayAccount.id == account_update.razorpay_account_id
        ).first()
        if not acc:
            raise HTTPException(status_code=400, detail="Invalid Razorpay account ID")

    app.razorpay_account_id = account_update.razorpay_account_id
    db.commit()
    db.refresh(app)
    return {
        "status": "success",
        "razorpay_account_id": app.razorpay_account_id,
        "razorpay_account_name": app.razorpay_account.name if app.razorpay_account else None
    }

@router.put("/apps/{app_id}")
async def update_app(
    app_id: str,
    app_update: schemas.AppUpdate,
    db: Session = Depends(get_db)
):
    app = db.query(models.App).filter(models.App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
        
    if app_update.name is not None:
        app.name = app_update.name
    if app_update.razorpay_account_id is not None:
        if app_update.razorpay_account_id:
            acc = db.query(models.RazorpayAccount).filter(
                models.RazorpayAccount.id == app_update.razorpay_account_id
            ).first()
            if not acc:
                raise HTTPException(status_code=400, detail="Invalid Razorpay account ID")
            app.razorpay_account_id = app_update.razorpay_account_id
        else:
            app.razorpay_account_id = None
            
    db.commit()
    db.refresh(app)
    return {
        "status": "success",
        "id": app.id,
        "name": app.name,
        "razorpay_account_id": app.razorpay_account_id,
        "razorpay_account_name": app.razorpay_account.name if app.razorpay_account else None
    }
