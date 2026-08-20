import hmac
import hashlib
import json
import time
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("portal_payment.webhook_dispatcher")

async def dispatch_payment_webhook(
    webhook_url: Optional[str],
    webhook_secret: Optional[str],
    event_type: str,
    payment_data: Dict[str, Any]
) -> bool:
    """
    Sends an HMAC-signed webhook notification to a registered client app.
    """
    if not webhook_url:
        logger.debug("No webhook_url configured for client app. Skipping dispatch.")
        return False

    timestamp = int(time.time())
    payload = {
        "event": event_type,
        "timestamp": timestamp,
        "data": payment_data
    }

    body_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    secret_bytes = (webhook_secret or "default_webhook_secret").encode('utf-8')

    signature = hmac.new(secret_bytes, body_bytes, hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(timestamp)
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, content=body_bytes, headers=headers)
            if response.is_success:
                logger.info(f"Successfully dispatched '{event_type}' webhook to {webhook_url}")
                return True
            else:
                logger.warning(
                    f"Webhook dispatch to {webhook_url} failed with status {response.status_code}: {response.text}"
                )
                return False
    except Exception as e:
        logger.error(f"Error dispatching webhook to {webhook_url}: {e}")
        return False
