"""Unit tests for TAZ wallet checkout flow."""
import os
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest

# Set up test env before any app imports
os.environ.setdefault('VAULT_KEY', 'test-vault-key-64chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
os.environ.setdefault('VAULT_URL', 'http://vault-test:8000')
os.environ.setdefault('VAULT_ESCROW_WALLET_ID', '00000000-0000-0000-0001-000000000001')


# ── vault_client unit tests ───────────────────────────────────────────────────

class TestVaultClientPhoneToUUID:
    def test_clean_uuid_passthrough(self):
        from app.services.vault.vault_client import create_wallet
        import uuid
        valid_uuid = str(uuid.uuid4())
        with patch('httpx.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=201, json=lambda: {'wallet_id': valid_uuid})
            result = create_wallet(valid_uuid)
            call_args = mock_post.call_args
            sent_uid = call_args[1]['json']['user_id']
            assert sent_uid == valid_uuid

    def test_phone_converted_to_uuid5(self):
        import uuid
        from app.services.vault.vault_client import create_wallet
        phone = '972501234567'
        expected_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, phone))
        with patch('httpx.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=201, json=lambda: {'wallet_id': expected_uuid})
            create_wallet(phone)
            call_args = mock_post.call_args
            sent_uid = call_args[1]['json']['user_id']
            assert sent_uid == expected_uuid


class TestVaultClientEscrowPayload:
    def test_escrow_lock_sends_order_id(self):
        from app.services.vault import vault_client as vault
        with patch('httpx.post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201,
                json=lambda: {'transaction_id': 'txn-123', 'status': 'locked'}
            )
            result = vault.escrow_lock('wallet-123', 'order-456', Decimal('70'))
            body = mock_post.call_args[1]['json']
            assert 'order_id' in body
            assert body['order_id'] == 'order-456'
            assert 'description' not in body  # old broken field should not be present


class TestCleanPhone:
    def test_israeli_landline_with_dashes(self):
        from app.api.v1.routes.public_taz_checkout import _clean_phone
        assert _clean_phone('03-629-9696') == '036299696'

    def test_israeli_mobile_converts_to_972(self):
        from app.api.v1.routes.public_taz_checkout import _clean_phone
        assert _clean_phone('0501234567') == '972501234567'

    def test_already_972_prefix(self):
        from app.api.v1.routes.public_taz_checkout import _clean_phone
        assert _clean_phone('972501234567') == '972501234567'


# ── morning_handler TAZ topup detection ─────────────────────────────────────

class TestTazTopupDetection:
    def _make_ctx(self, external_id, status='SUCCESS', amount=70):
        return {
            'status': status,
            'amount': amount,
            'currency': 'ILS',
            'external_id': external_id,
            'transaction_id': 'txn-e2e-test',
        }

    def test_non_topup_external_id_ignored(self):
        from app.api.v1.payments.morning_handler import handle_taz_wallet_topup
        ctx = self._make_ctx('auto-tier:some-intake-id')
        ctx['status'] = 'SUCCESS'
        result = handle_taz_wallet_topup(ctx)
        assert result.get('ok') is True
        assert 'not a taz-topup event' in str(result.get('detail', ''))

    def test_non_success_status_returns_ok(self):
        from app.api.v1.payments.morning_handler import handle_taz_wallet_topup
        ctx = self._make_ctx('taz-topup:972501234567:ref123', status='FAILED')
        result = handle_taz_wallet_topup(ctx)
        assert result.get('ok') is True
        assert 'non-success' in str(result.get('detail', ''))

    def test_bad_external_id_format_returns_error(self):
        from app.api.v1.payments.morning_handler import handle_taz_wallet_topup
        ctx = self._make_ctx('taz-topup:onlyone')  # only 2 parts, need 3
        result = handle_taz_wallet_topup(ctx)
        assert result.get('ok') is False

    def test_dispatcher_routes_taz_topup(self):
        from app.api.v1.payments.morning_handler import handle_morning_event
        body = {'type': 'sale', 'status': 'SUCCESS', 'externalId': 'taz-topup:972501234567:ref123', 'amount': 50}
        parsed = {'type': 'sale', 'status': 'SUCCESS', 'external_id': 'taz-topup:972501234567:ref123', 'amount': 50, 'transaction_id': 'txn-1', 'currency': 'ILS'}
        with patch('app.api.v1.payments.morning_handler.handle_taz_wallet_topup') as mock_topup:
            mock_topup.return_value = {'ok': True, 'topped_up': 50}
            result = handle_morning_event(body, parsed)
            mock_topup.assert_called_once()


# ── business verification ─────────────────────────────────────────────────────

class TestBusinessVerification:
    def test_active_business_verified(self):
        from app.api.v1.routes.public_taz_checkout import _is_biz_verified
        biz = MagicMock(status='active')
        assert _is_biz_verified(biz) is True

    def test_paid_business_verified(self):
        from app.api.v1.routes.public_taz_checkout import _is_biz_verified
        biz = MagicMock(status='paid')
        assert _is_biz_verified(biz) is True

    def test_draft_business_not_verified(self):
        from app.api.v1.routes.public_taz_checkout import _is_biz_verified
        biz = MagicMock(status='draft_created')
        assert _is_biz_verified(biz) is False

    def test_pending_business_not_verified(self):
        from app.api.v1.routes.public_taz_checkout import _is_biz_verified
        biz = MagicMock(status='pending')
        assert _is_biz_verified(biz) is False
