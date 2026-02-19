"""
Security utilities: password hashing, session token creation and verification.
Uses bcrypt for passwords and HMAC-SHA256 for stateless session tokens.
No external auth service needed — perfect for HF Spaces.
"""
import hmac
import hashlib
import secrets
import time
from typing import Optional

import bcrypt

from app.core.config import SECRET_KEY, SESSION_EXPIRE_HOURS


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Session tokens ────────────────────────────────────────────────────────────
# Token format: "{user_id}:{expires_timestamp}:{hmac_signature}"

def create_session_token(user_id: str) -> str:
    """Create a signed session token valid for SESSION_EXPIRE_HOURS."""
    expires = int(time.time()) + SESSION_EXPIRE_HOURS * 3600
    payload = f"{user_id}:{expires}"
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_session_token(token: str) -> Optional[str]:
    """
    Validate a session token.
    Returns the user_id string if valid, else None.
    """
    try:
        parts = token.rsplit(":", 1)
        if len(parts) != 2:
            return None
        payload, sig = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        user_id, expires_str = payload.split(":", 1)
        if int(time.time()) > int(expires_str):
            return None
        return user_id
    except Exception:
        return None
