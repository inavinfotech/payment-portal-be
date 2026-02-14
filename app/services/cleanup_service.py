from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models
from datetime import datetime, timedelta
import pytz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_stale_payments():
    """
    Finds payments with status 'created' that are older than 20 minutes
    and updates their status to 'unprocessed'.
    """
    db: Session = SessionLocal()
    try:
        # Time threshold: 20 minutes ago in IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_tz)
        threshold_time = now_ist - timedelta(minutes=20)
        
        # Query for stale payments
        stale_payments = db.query(models.Payment).filter(
            models.Payment.status == "created",
            models.Payment.created_at < threshold_time
        ).all()
        
        if not stale_payments:
            return

        logger.info(f"Found {len(stale_payments)} stale payments. Updating to 'unprocessed'.")
        
        for payment in stale_payments:
            payment.status = "unprocessed"
            
        db.commit()
    except Exception as e:
        logger.error(f"Error processing stale payments: {e}")
        db.rollback()
    finally:
        db.close()
