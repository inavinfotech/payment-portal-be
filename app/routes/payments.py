from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..auth import get_current_app
from .. import schemas, models, razorpay_service
from ..config import settings

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create-order", response_model=schemas.PaymentResponse)
async def create_order(
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_app: models.App = Depends(get_current_app)
):
    if payment.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )

    # Create Razorpay Order
    try:
        order = razorpay_service.create_order(
            amount=payment.amount,
            currency=payment.currency,
            notes=payment.metadata_info
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay order creation failed"
        )

    db_amount = payment.amount
    if payment.currency == "INR":
        db_amount = payment.amount // 100

    db_payment = models.Payment(
        app_id=current_app.id,
        user_id=payment.user_id,
        amount=db_amount,
        currency=payment.currency,
        plan_type=payment.plan_type,
        razorpay_order_id=order.get("id"),
        status=order.get("status", "created"),
        metadata_info=payment.metadata_info
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    return schemas.PaymentResponse(
        id=db_payment.id,
        razorpay_order_id=db_payment.razorpay_order_id,
        amount=db_payment.amount,
        currency=db_payment.currency,
        status=db_payment.status,
        created_at=db_payment.created_at,
        key_id=settings.RAZORPAY_KEY_ID
    )

@router.post("/verify-payment", response_model=schemas.PaymentVerificationResponse)
async def verify_payment(
    verify_data: schemas.PaymentVerify,
    db: Session = Depends(get_db)
):
    # Fetch payment
    payment = db.query(models.Payment).filter(
        models.Payment.razorpay_order_id == verify_data.razorpay_order_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
        
    # Prevent duplicate verification
    if payment.status == "paid":
        return {"status": "success", "message": "Payment already verified"}

    # Verify Signature
    params_dict = {
        'razorpay_order_id': verify_data.razorpay_order_id,
        'razorpay_payment_id': verify_data.razorpay_payment_id,
        'razorpay_signature': verify_data.razorpay_signature
    }
    
    # Check signature validity
    is_valid = razorpay_service.verify_payment_signature(params_dict)
    
    if is_valid is None: 
         # client.utility.verify_payment_signature returns None on success, raises error on failure
         # But our wrapper returns True/False for mock, and True/False for real (if we modify it to catch error)
         # Wait, client.utility.verify_payment_signature returns None if valid, raises SignatureVerificationError if invalid.
         # My wrapper returns True/False.
         pass
         
    if not is_valid:
        payment.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Signature"
        )

    # Update Payment Status
    payment.status = "paid"
    payment.razorpay_payment_id = verify_data.razorpay_payment_id
    payment.paid_at = func.now()
    
    db.commit()
    db.refresh(payment)
    
    return schemas.PaymentVerificationResponse(
        success=True,
        message="Payment verified successfully",
        data=schemas.PaymentVerificationData(
            verification_status="verified",
            payment_id=payment.razorpay_payment_id,
            order_id=payment.razorpay_order_id,
            amount_paid=payment.amount,
            currency=payment.currency,
            paid_at=payment.paid_at,
            metadata=payment.metadata_info
        )
    )

@router.post("/fail")
async def fail_payment(
    fail_data: schemas.PaymentFail,
    db: Session = Depends(get_db)
):
    payment = db.query(models.Payment).filter(
        models.Payment.razorpay_order_id == fail_data.razorpay_order_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
        
    payment.status = "failed"
    if fail_data.metadata:
        # Merge or overwrite metadata
        current_meta = payment.metadata_info or {}
        current_meta.update(fail_data.metadata)
        current_meta["failure_reason"] = fail_data.reason
        payment.metadata_info = current_meta
    
    db.commit()
    return {"status": "success", "message": "Payment marked as failed"}

@router.post("/cancel")
async def cancel_payment(
    cancel_data: schemas.PaymentCancel,
    db: Session = Depends(get_db)
):
    payment = db.query(models.Payment).filter(
        models.Payment.razorpay_order_id == cancel_data.razorpay_order_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
        
    if payment.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot cancel a failed payment"
        )
        
    payment.status = "cancelled"
    
    # Store reason in metadata
    current_meta = payment.metadata_info or {}
    current_meta["cancellation_reason"] = cancel_data.reason
    payment.metadata_info = current_meta
    
    db.commit()
    return {"status": "success", "message": "Payment marked as cancelled"}

@router.get("/payment-status/{order_id}", response_model=schemas.PaymentResponse)
async def get_payment_status(order_id: str, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(
        models.Payment.razorpay_order_id == order_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return schemas.PaymentResponse(
        id=payment.id,
        razorpay_order_id=payment.razorpay_order_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        created_at=payment.created_at,
        key_id=settings.RAZORPAY_KEY_ID
    )

@router.get("/")
async def read_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_app: models.App = Depends(get_current_app) # Require admin authentication
):
    payments = db.query(models.Payment).filter(models.Payment.app_id == current_app.id).offset(skip).limit(limit).all()
    # Return list of schemas.PaymentResponse? No, the frontend expects a list.
    # The existing endpoint just returns a mock. I should probably fix it to return real data too,
    # but the task is about export.
    # Wait, the existing endpoint returns `[{"payment_id": "1", "amount": 100}]`.
    # And the frontend calls `/admin/payments`.
    # Let me check `backend/app/main.py` to see how routes are included.
    # The frontend code says: `${import.meta.env.VITE_API_BASE_URL}/admin/payments`
    # I need to see where `/admin/payments` is defined.
    # The current `payments.py` has `prefix="/payments"`. 
    # If `main.py` includes it under `/admin`, then it's `/admin/payments`.
    return payments

@router.get("/export")
async def export_payments(
    format: str,
    db: Session = Depends(get_db),
    current_app: models.App = Depends(get_current_app)
):
    payments = db.query(models.Payment).filter(models.Payment.app_id == current_app.id).all()
    
    # Convert to list of dicts
    data = []
    for p in payments:
        data.append({
            "Razorpay Order ID": p.razorpay_order_id,
            "Razorpay Payment ID": p.razorpay_payment_id,
            "Amount": p.amount,
            "Currency": p.currency,
            "Status": p.status,
            "Date": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
            "Paid At": p.paid_at.strftime("%Y-%m-%d %H:%M:%S") if p.paid_at else "",
            "Failure Reason": p.metadata_info.get("failure_reason", "") if p.metadata_info else ""
        })
        
    if not data:
         # Handle empty data case, maybe return empty file or 404? 
         # Exporting empty file is better.
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

