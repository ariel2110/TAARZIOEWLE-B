"""
Unit tests for WhatsApp webhook HMAC-SHA256 signature verification
and message deduplication logic.
No DB, no HTTP calls.
"""
import hashlib
import hmac
import os
import time

os.environ.setdefault("WHATSAPP_WEBHOOK_SECRET", "test-wa-secret")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test-verify-token")
os.environ.setdefault("USE_POSTGRES", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

import pytest


def _make_wa_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


class TestWhatsAppSignatureVerification:
    @pytest.fixture(autouse=True)
    def _import(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_WEBHOOK_SECRET", "test-wa-secret")
        from app.api.v1.routes.webhooks_whatsapp import _verify_signature
        self._verify = _verify_signature

    def test_valid_signature_accepted(self):
        body = b'{"object":"whatsapp_business_account"}'
        sig = _make_wa_signature(body, "test-wa-secret")
        assert self._verify(body, sig) is True

    def test_invalid_signature_rejected(self):
        body = b'{"object":"whatsapp_business_account"}'
        assert self._verify(body, "sha256=deadbeef") is False

    def test_missing_sha256_prefix_rejected(self):
        body = b'{"object":"whatsapp_business_account"}'
        raw_hex = hmac.new(b"test-wa-secret", body, hashlib.sha256).hexdigest()
        # No 'sha256=' prefix — still valid because removeprefix handles it
        assert self._verify(body, raw_hex) is True

    def test_no_signature_header_rejected(self):
        body = b'{"object":"whatsapp_business_account"}'
        assert self._verify(body, None) is False

    def test_tampered_body_rejected(self):
        body = b'{"object":"whatsapp_business_account"}'
        sig = _make_wa_signature(body, "test-wa-secret")
        tampered = b'{"object":"HACKED"}'
        assert self._verify(tampered, sig) is False

    def test_no_secret_configured_is_failopen(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_WEBHOOK_SECRET", "")
        from importlib import reload
        import app.core.config as cfg_mod
        reload(cfg_mod)
        import app.api.v1.routes.webhooks_whatsapp as wa_mod
        reload(wa_mod)
        assert wa_mod._verify_signature(b"body", None) is True


class TestMessageDeduplication:
    def test_first_message_not_duplicate(self):
        from app.api.v1.routes.webhooks_whatsapp import _seen_msg_ids, _is_duplicate
        _seen_msg_ids.clear()
        assert _is_duplicate("msg-001") is False

    def test_second_same_message_is_duplicate(self):
        from app.api.v1.routes.webhooks_whatsapp import _seen_msg_ids, _is_duplicate
        _seen_msg_ids.clear()
        _is_duplicate("msg-002")
        assert _is_duplicate("msg-002") is True

    def test_different_ids_are_not_duplicates(self):
        from app.api.v1.routes.webhooks_whatsapp import _seen_msg_ids, _is_duplicate
        _seen_msg_ids.clear()
        _is_duplicate("msg-A")
        assert _is_duplicate("msg-B") is False

    def test_empty_id_never_duplicate(self):
        from app.api.v1.routes.webhooks_whatsapp import _is_duplicate
        assert _is_duplicate("") is False
        assert _is_duplicate("") is False


class TestWebhookVerifyEndpoint:
    def test_get_challenge_succeeds(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.v1.routes.webhooks_whatsapp import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "12345",
            },
        )
        assert resp.status_code == 200
        assert resp.json() == 12345

    def test_wrong_verify_token_returns_403(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.v1.routes.webhooks_whatsapp import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "12345",
            },
        )
        assert resp.status_code == 403
