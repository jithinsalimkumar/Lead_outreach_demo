"""
Encryption service — Fernet symmetric encryption for API key storage.

Uses the ENCRYPTION_KEY from environment variables. If no key is set,
a default (insecure) key is used — this is fine for dev but must be
replaced in production.
"""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    """
    Get a Fernet instance using the configured encryption key.

    The ENCRYPTION_KEY from env should be a valid Fernet key (base64-encoded 32 bytes).
    If the provided key isn't valid Fernet format, we derive a valid key from it
    using SHA-256 to avoid crashes with user-provided strings.
    """
    key = settings.ENCRYPTION_KEY
    if not key:
        # Fallback for dev — NOT SECURE, just prevents crashes
        key = "dev-only-insecure-key-change-me"

    try:
        # Try using the key directly (if it's already a valid Fernet key)
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        # Derive a valid Fernet key from the provided string
        # SHA-256 gives us 32 bytes, base64-encode it for Fernet
        derived = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(derived)
        return Fernet(fernet_key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string and return the encrypted value as a string."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """Decrypt an encrypted string back to plaintext."""
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()


def mask_value(value: str) -> str:
    """
    Mask a sensitive value for display purposes.
    Shows only the last 4 characters: ****abcd
    """
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]
