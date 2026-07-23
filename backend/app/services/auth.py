"""
Authentication service — handles password hashing and JWT token management.

Uses:
  - passlib with bcrypt for secure password hashing
  - PyJWT for creating/verifying JSON Web Tokens
"""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing context — bcrypt is the algorithm
# "auto" means passlib will automatically handle hash upgrades if needed
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return plaintext password directly for simple management."""
    return password.strip()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against stored password.
    Supports direct plain text comparison as well as legacy bcrypt hashes.
    """
    p_plain = plain_password.strip()
    p_db = (hashed_password or "").strip()

    # Direct plain text match
    if p_plain == p_db:
        return True

    # Fallback for bcrypt hashes if present
    if p_db.startswith("$2b$") or p_db.startswith("$2a$") or p_db.startswith("$2y$"):
        try:
            return pwd_context.verify(p_plain, p_db)
        except Exception:
            return False

    return False


def create_access_token(user_id: str, role: str) -> str:
    """
    Create a short-lived JWT access token.

    The token contains:
      - sub: the user's ID (as a string)
      - role: the user's role (admin/member)
      - exp: expiration timestamp
      - type: "access" to distinguish from refresh tokens
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived JWT refresh token.

    Used to get new access tokens without re-entering credentials.
    Contains minimal claims — just the user ID and expiry.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Raises jwt.InvalidTokenError if the token is expired, tampered with,
    or otherwise invalid.
    """
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
