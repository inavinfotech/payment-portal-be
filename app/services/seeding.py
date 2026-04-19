from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, auth
import logging

logger = logging.getLogger("payment-service")

def seed_data():
    db = SessionLocal()
    try:
        # Seed Website Application
        website_api_key = "tiana_web_key_12345"
        website_api_secret = "tiana_web_secret_67890"
        
        existing_app = db.query(models.App).filter(models.App.api_key == website_api_key).first()
        if not existing_app:
            logger.info("Seeding website application to payment portal...")
            new_app = models.App(
                name="TianaLuxora Website",
                api_key=website_api_key,
                api_secret_hash=auth.get_password_hash(website_api_secret),
                is_active=True,
                is_live_mode=False,
                allowed_domains="*"
            )
            db.add(new_app)
            
            # Also seed a system setting for global payment switch
            global_setting = models.SystemSetting(key="global_payment_enabled", value="true")
            db.add(global_setting)
            
            db.commit()
            logger.info("Website application seeding complete for payment portal.")
        else:
            logger.info("Website application already exists in payment portal.")
            
    except Exception as e:
        logger.error(f"Error seeding payment portal data: {e}")
        db.rollback()
    finally:
        db.close()
