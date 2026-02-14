from app.database import SessionLocal
from app import models
from datetime import datetime
import pytz
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

def verify_ist():
    db = SessionLocal()
    try:
        # Create a new payment (should get IST timestamp by default)
        
        # We need a valid app
        app = db.query(models.App).first()
        if not app:
            logging.error("No apps found in DB to test.")
            return

        test_payment = models.Payment(
            app_id=app.id,
            order_id="order_test_ist_123",
            amount=100.0,
            currency="INR",
            user_id="user_test"
        )
        db.add(test_payment)
        db.commit()
        db.refresh(test_payment)
        
        created_at = test_payment.created_at
        logging.info(f"Payment created_at: {created_at}")
        logging.info(f"Timezone info: {created_at.tzinfo}")
        
        # Check if approx correct (IST is UTC+5:30)
        utc_now = datetime.now(pytz.utc)
        ist_now = datetime.now(pytz.timezone('Asia/Kolkata'))
        
        logging.info(f"Current UTC time: {utc_now}")
        logging.info(f"Current IST time: {ist_now}")
        
        # Simple check: created_at should be close to ist_now
        diff = abs((ist_now - created_at).total_seconds())
        if diff < 10: # Allow 10 seconds difference
             logging.info("SUCCESS: created_at matches current IST time.")
        else:
             logging.error(f"FAILURE: created_at {created_at} deviates from IST {ist_now} by {diff} seconds.")

    except Exception as e:
        logging.error(f"Test failed: {e}")
    finally:
        # Cleanup
        if 'test_payment' in locals():
            db.delete(test_payment)
            db.commit()
        db.close()

if __name__ == "__main__":
    verify_ist()
