"""Internal HTTP client for the Taz Currency Vault."""
from __future__ import annotations
import logging
import os
from decimal import Decimal
import httpx

logger = logging.getLogger(__name__)

VAULT_URL = os.environ.get('VAULT_URL', 'http://76.13.42.13:8000')
VAULT_KEY = os.environ.get('VAULT_KEY', '')
_TIMEOUT = 10.0


def _h() -> dict:
    return {'X-Vault-Internal-Key': VAULT_KEY, 'Content-Type': 'application/json'}


def health() -> bool:
    try:
        r = httpx.get(f'{VAULT_URL}/health', timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False


def get_balance(wallet_id: str) -> Decimal | None:
    if not VAULT_KEY or not wallet_id:
        return None
    try:
        r = httpx.get(f'{VAULT_URL}/balance/{wallet_id}', headers=_h(), timeout=_TIMEOUT)
        if r.status_code == 200:
            return Decimal(str(r.json().get('balance', 0)))
        logger.warning('[Vault] get_balance %s HTTP %s', wallet_id[:8], r.status_code)
    except Exception as exc:
        logger.warning('[Vault] get_balance error: %s', exc)
    return None


def create_wallet(user_id: str) -> str | None:
    if not VAULT_KEY:
        return None
    import uuid as _uuid
    try:
        _uuid.UUID(user_id)
        uid = user_id
    except (ValueError, AttributeError):
        uid = str(_uuid.uuid5(_uuid.NAMESPACE_OID, user_id))
    try:
        r = httpx.post(f'{VAULT_URL}/wallets/create', json={'user_id': uid}, headers=_h(), timeout=_TIMEOUT)
        if r.status_code in (200, 201):
            data = r.json()
            return str(data.get('wallet_id') or data.get('id') or uid)
        logger.warning('[Vault] create_wallet HTTP %s: %s', r.status_code, r.text[:100])
    except Exception as exc:
        logger.warning('[Vault] create_wallet error: %s', exc)
    return None


def topup_wallet(wallet_id: str, amount: Decimal, reference: str = '') -> dict | None:
    if not VAULT_KEY or not wallet_id or amount <= 0:
        return None
    try:
        r = httpx.post(
            f'{VAULT_URL}/wallets/topup',
            json={'wallet_id': wallet_id, 'amount': str(amount), 'reference': reference},
            headers=_h(), timeout=_TIMEOUT,
        )
        if r.status_code in (200, 201):
            return r.json()
        logger.warning('[Vault] topup_wallet HTTP %s: %s', r.status_code, r.text[:100])
    except Exception as exc:
        logger.warning('[Vault] topup_wallet error: %s', exc)
    return None


def escrow_lock(buyer_wallet_id: str, order_id: str, amount: Decimal) -> dict | None:
    escrow_wallet = os.environ.get('VAULT_ESCROW_WALLET_ID', '')
    if not VAULT_KEY or not buyer_wallet_id or not escrow_wallet or amount <= 0:
        logger.warning('[Vault] escrow_lock skipped: key=%s escrow=%s amount=%s', bool(VAULT_KEY), bool(escrow_wallet), amount)
        return None
    try:
        r = httpx.post(
            f'{VAULT_URL}/escrow/lock',
            json={'buyer_wallet_id': buyer_wallet_id, 'escrow_wallet_id': escrow_wallet,
                  'order_id': order_id, 'amount': str(amount)},
            headers=_h(), timeout=_TIMEOUT,
        )
        if r.status_code in (200, 201):
            return r.json()
        logger.warning('[Vault] escrow_lock HTTP %s: %s', r.status_code, r.text[:100])
    except Exception as exc:
        logger.warning('[Vault] escrow_lock error: %s', exc)
    return None


def escrow_release(order_id: str, driver_wallet_id: str) -> dict | None:
    if not VAULT_KEY or not order_id:
        return None
    try:
        r = httpx.post(
            f'{VAULT_URL}/escrow/release',
            json={'order_id': order_id, 'driver_wallet_id': driver_wallet_id},
            headers=_h(), timeout=_TIMEOUT,
        )
        if r.status_code in (200, 201):
            return r.json()
        logger.warning('[Vault] escrow_release HTTP %s: %s', r.status_code, r.text[:100])
    except Exception as exc:
        logger.warning('[Vault] escrow_release error: %s', exc)
    return None
