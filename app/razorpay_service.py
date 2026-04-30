import razorpay
from .config import settings
import uuid

def _get_keys_for_mode(is_live_mode: bool):
    if is_live_mode:
        return settings.RAZORPAY_LIVE_KEY_ID, settings.RAZORPAY_LIVE_KEY_SECRET
    return settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET

def _get_client(is_live_mode: bool):
    if settings.FORCE_MOCK_PAYMENTS:
        return None
    print(is_live_mode)
    key_id, key_secret = _get_keys_for_mode(is_live_mode)
    if not key_id or not key_secret:
        return None
    client = razorpay.Client(auth=(key_id, key_secret))
    # Optional: configure timeout if supported by backend requests session
    # Most versions of razorpay-python don't have a direct set_timeout, 
    # but they use requests session which we can sometimes access or just rely on global defaults.
    # However, setting it directly on the client if it supports it:
    if hasattr(client, 'set_timeout'):
        client.set_timeout(20)
    return client

def create_order(amount: int, currency: str = "INR", receipt: str = None, notes: dict = None, is_live_mode: bool = False):
    client = _get_client(is_live_mode)
    if not client:
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

def verify_payment_signature(params_dict, is_live_mode: bool = False):
    client = _get_client(is_live_mode)
    if not client:
        # Mock mode - always true for now, or check for specific mock signature
        return True
        
    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except Exception as e:
        print(f"Razorpay Verification Error: {e}")
        return False
