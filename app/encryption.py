"""
Fernet-based encryption utility for storing sensitive data (e.g., Razorpay secrets) in the database.
Uses the app's SECRET_KEY to derive a Fernet-compatible key.
"""
import base64
import hashlib
from cryptography.fernet import Fernet

_fernet_instance = None

def _get_fernet():
    global _fernet_instance
    if _fernet_instance is None:
        from .config import settings
        # Derive a 32-byte key from SECRET_KEY using SHA-256, then base64-encode for Fernet
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        _fernet_instance = Fernet(fernet_key)
    return _fernet_instance

def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string and return the ciphertext as a UTF-8 string."""
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode()).decode()

def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string and return the original plaintext."""
    if not ciphertext:
        return ""
    return _get_fernet().decrypt(ciphertext.encode()).decode()
