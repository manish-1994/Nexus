import base64
import os
from cryptography.fernet import Fernet


def get_encryption_key() -> bytes:
    """Get encryption key from environment."""
    key = os.getenv("API_KEY_ENCRYPTION_KEY", "change-me-in-production")
    # Ensure key is valid for Fernet (must be 32 url-safe base64-encoded bytes)
    if len(key) < 32:
        key = key.ljust(32, "0")
    return base64.urlsafe_b64encode(key[:32].encode())


def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key."""
    f = Fernet(get_encryption_key())
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key."""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_key.encode()).decode()
