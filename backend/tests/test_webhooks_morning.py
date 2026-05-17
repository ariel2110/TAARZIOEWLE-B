"""
Unit tests for Morning webhook HMAC-SHA256 signature verification.
Tests MorningService.verify_webhook_signature directly — no HTTP, no DB.
"""
import hashlib
import hmac
import os

os.environ.setdefault("MORNING_WEBHOOK_SECRET", "test-morning-secret")
os.environ.setdefault("USE_POSTGRES", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

import pytest


def _make_signature(body: bytes, secret: str) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()


class TestMorningSignatureVerification:
    @pytest.fixture(autouse=True)
    def _service(self, monkeypatch):
        monkeypatch.setenv("MORNING_WEBHOOK_SECRET", "test-morning-secret")
        from app.services.morning_service import MorningService
        self.svc = MorningService()

    def test_valid_signature_accepted(self):
        body = b'{"eventType":"payment.success","amount":39}'
        sig = _make_signature(body, "test-morning-secret")
        assert self.svc.verify_webhook_signature(body, sig) is True

    def test_invalid_signature_rejected(self):
        body = b'{"eventType":"payment.success","amount":39}'
        assert self.svc.verify_webhook_signature(body, "deadbeef") is False

    def test_tampered_body_rejected(self):
        body = b'{"eventType":"payment.success","amount":39}'
        sig = _make_signature(body, "test-morning-secret")
        tampered = b'{"eventType":"payment.success","amount":999}'
        assert self.svc.verify_webhook_signature(tampered, sig) is False

    def test_empty_signature_with_secret_configured_rejected(self):
        body = b'{"amount":39}'
        assert self.svc.verify_webhook_signature(body, "") is False

    def test_no_secret_configured_is_failopen(self, monkeypatch):
        monkeypatch.setenv("MORNING_WEBHOOK_SECRET", "")
        monkeypatch.setenv("MORNING_API_SECRET", "")
        # Reload service with no secret
        from importlib import reload
        import app.core.config as cfg_mod
        reload(cfg_mod)
        from app.services import morning_service as ms_mod
        reload(ms_mod)
        svc = ms_mod.MorningService()
        assert svc.verify_webhook_signature(b"body", "anything") is True

    def test_signature_is_case_insensitive(self):
        body = b'{"amount":39}'
        sig = _make_signature(body, "test-morning-secret").upper()
        assert self.svc.verify_webhook_signature(body, sig) is True


class TestMorningParseWebhook:
    @pytest.fixture(autouse=True)
    def _service(self):
        from app.services.morning_service import MorningService
        self.svc = MorningService()

    def test_parse_success_event(self):
        body = {
            "eventType": "payment.success",
            "transactionId": "txn-123",
            "externalId": "ext-456",
            "amount": 39,
            "status": "SUCCESS",
        }
        result = self.svc.parse_webhook(body)
        assert result is not None
        assert result["transaction_id"] == "txn-123"
        assert result["amount"] == 39

    def test_parse_unknown_event_returns_none(self):
        result = self.svc.parse_webhook({"foo": "bar"})
        assert result is None
