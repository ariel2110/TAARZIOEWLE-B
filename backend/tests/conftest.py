"""
Shared pytest configuration and fixtures for the TAZO-WEB backend test suite.
No database connection is required — all tests in this suite are unit-level.
"""
import os
import pytest

# ── Patch settings before any app import ────────────────────────────────────
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("USE_POSTGRES", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("INTERNAL_KEY", "")
os.environ.setdefault("ODIN_JWT_PUBLIC_KEY", "")
os.environ.setdefault("MORNING_WEBHOOK_SECRET", "test-morning-secret")
os.environ.setdefault("WHATSAPP_WEBHOOK_SECRET", "test-wa-secret")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test-verify-token")
