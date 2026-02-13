import razorpay
from .config import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Placeholder for Razorpay service functions
import uuid

def create_order(amount: int, currency: str = "INR", receipt: str = None, notes: dict = None):
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        # Mock mode
        return {
            "id": f"order_mock_{uuid.uuid4().hex[:8]}",
            "entity": "order",
            "amount": amount,
            "amount_paid": 0,
            "amount_due": amount,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "attempts": 0,
            "notes": notes,
            "created_at": 1234567890
        }

    data = {
        "amount": amount,
        "currency": currency,
        "receipt": receipt,
        "notes": notes,
        "payment_capture": 1
    }
    try:
        return client.order.create(data=data)
    except Exception as e:
        print(f"Razorpay Error: {e}")
        raise e

def verify_payment_signature(params_dict):
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        # Mock mode - always true for now, or check for specific mock signature
        return True
        
    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except Exception as e:
        print(f"Razorpay Verification Error: {e}")
        return False
