import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings


def create_access_token(subject: str, role: str = 'admin') -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {'sub': subject, 'role': role, 'exp': expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


# ── Password hashing (bcrypt, with silent SHA-256 migration) ─────────────────
# Legacy hashes are 64-char hex strings (SHA-256).
# New hashes start with '$2b$' (bcrypt).

def _is_legacy_hash(h: str) -> bool:
    """Return True if hash is old-style SHA-256 hex (64 lowercase hex chars)."""
    return len(h) == 64 and all(c in '0123456789abcdef' for c in h)


def _sha256_hex(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash (bcrypt or legacy SHA-256)."""
    if _is_legacy_hash(password_hash):
        # Legacy SHA-256 comparison
        return _sha256_hex(password) == password_hash
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def needs_rehash(password_hash: str) -> bool:
    """Return True if the hash is legacy SHA-256 and should be upgraded to bcrypt."""
    return _is_legacy_hash(password_hash)
