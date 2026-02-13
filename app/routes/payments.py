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
async def read_payments():
    return [{"payment_id": "1", "amount": 100}]
