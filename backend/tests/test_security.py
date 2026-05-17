"""
Unit tests for app/core/security.py
Covers: JWT round-trip, expired tokens, password hashing, legacy SHA-256 migration.
No DB required.
"""
import time
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt as jose_jwt

import os
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("USE_POSTGRES", "false")

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    needs_rehash,
    _is_legacy_hash,
    _sha256_hex,
)


class TestJWT:
    def test_create_and_decode_roundtrip(self):
        token = create_access_token("user@example.com", role="admin")
        payload = decode_access_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "admin"

    def test_default_role_is_admin(self):
        token = create_access_token("user@example.com")
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        from jose import jwt as _jwt, JWTError
        expired_payload = {
            "sub": "user@example.com",
            "role": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token = _jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(Exception):
            decode_access_token(token)

    def test_tampered_token_raises(self):
        token = create_access_token("user@example.com")
        tampered = token[:-4] + "XXXX"
        with pytest.raises(Exception):
            decode_access_token(tampered)

    def test_wrong_secret_raises(self):
        from jose import jwt as _jwt
        token = _jwt.encode({"sub": "x"}, "wrong-secret", algorithm="HS256")
        with pytest.raises(Exception):
            decode_access_token(token)


class TestPasswordHashing:
    def test_bcrypt_hash_and_verify(self):
        pw = "MySecurePassword123!"
        hashed = hash_password(pw)
        assert hashed.startswith("$2b$")
        assert verify_password(pw, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_needs_rehash_for_bcrypt_is_false(self):
        hashed = hash_password("password")
        assert not needs_rehash(hashed)

    def test_legacy_sha256_detection(self):
        sha256_hash = _sha256_hex("password")
        assert _is_legacy_hash(sha256_hash)
        assert not _is_legacy_hash("$2b$12$shortbcrypt")

    def test_legacy_sha256_verify(self):
        sha256_hash = _sha256_hex("legacy-password")
        assert verify_password("legacy-password", sha256_hash)
        assert not verify_password("wrong", sha256_hash)

    def test_needs_rehash_true_for_legacy(self):
        sha256_hash = _sha256_hex("password")
        assert needs_rehash(sha256_hash)
