"""TAZ wallet checkout flow for sites built on TAZO-WEB.

Flow:
  POST /public/taz-checkout
    1. Look up business by phone → check status == 'active'|'paid' (verified)
    2. Look up / create customer wallet by phone
    3. Check vault balance vs order total
    4. Sufficient  → return {approved: true, wallet_id, balance}
    5. Insufficient → generate Morning top-up link for exact shortfall
                    → store pending_order_ref on wallet
                    → return {needs_topup: true, amount_needed, topup_url}

  POST /public/taz-debit   (called after customer confirms)
    - Escrow-lock TAZ from buyer wallet
    - Forward order to tazo-sync
"""
from __future__ import annotations

import json
import os
import logging
import re
import uuid
from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.business import Business
from app.models.customer_taz_wallet import CustomerTazWallet
from app.services.vault import vault_client as vault

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/public', tags=['taz-checkout'])

_MORNING_BASE = 'https://api.morning.co.il/v1'
_MORNING_TIMEOUT = 15


# ── helpers ──────────────────────────────────────────────────────────────────

def _clean_phone(raw: str) -> str:
    p = re.sub(r'\D', '', raw or '')
    if p.startswith('0') and len(p) == 10:
        p = '972' + p[1:]
    return p


def _is_biz_verified(business: Business) -> bool:
    return business.status in ('active', 'paid')


def _get_or_create_wallet(db: Session, phone: str) -> CustomerTazWallet:
    rec = db.query(CustomerTazWallet).filter(CustomerTazWallet.phone == phone).first()
    if rec:
        return rec
    # Create new vault wallet
    wallet_id = vault.create_wallet(user_id=phone)
    if not wallet_id:
        wallet_id = str(uuid.uuid4())  # fallback local UUID until vault is reachable
    rec = CustomerTazWallet(phone=phone, wallet_id=wallet_id)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def _create_morning_topup_link(customer_phone: str, customer_name: str, amount_nis: Decimal, ref: str) -> str | None:
    """Create Morning payment link for TAZ top-up. Returns URL or None."""
    if not settings.morning_api_key or not settings.morning_api_secret:
        return settings.morning_fixed_payment_url
    import base64
    token = base64.b64encode(f'{settings.morning_api_key}:{settings.morning_api_secret}'.encode()).decode()
    payload = {
        'description': f'TAZO — טעינת ארנק {float(amount_nis):.0f} ₪',
        'price': float(amount_nis),
        'currency': 'ILS',
        'externalId': f'taz-topup:{customer_phone}:{ref}',
        'custom': ref,
        'successUrl': f'{settings.morning_success_url}?taz=1&ref={ref}',
        'cancelUrl': settings.morning_cancel_url,
        'client': {'name': customer_name or 'לקוח', 'phone': customer_phone},
    }
    try:
        r = httpx.post(
            f'{_MORNING_BASE}/paymentlinks',
            json=payload,
            headers={'Authorization': f'Basic {token}', 'Content-Type': 'application/json'},
            timeout=_MORNING_TIMEOUT,
        )
        if r.status_code in (200, 201):
            data = r.json()
            url = data.get('url') or data.get('link') or data.get('paymentUrl') or data.get('checkout_url')
            if url:
                return url
        logger.warning('[TazCheckout] Morning link HTTP %s: %s', r.status_code, r.text[:200])
    except Exception as exc:
        logger.warning('[TazCheckout] Morning link error: %s', exc)
    return settings.morning_fixed_payment_url


# ── schemas ───────────────────────────────────────────────────────────────────

class TazCheckoutIn(BaseModel):
    customer_phone: str
    customer_name: str | None = None
    business_phone: str
    items: list | None = None
    total: float
    order_type: str | None = 'delivery'
    notes: str | None = None


class TazDebitIn(BaseModel):
    customer_phone: str
    customer_name: str | None = None
    business_phone: str
    business_name: str | None = None
    order_id: str
    amount: float
    items: list | None = None
    order_type: str | None = 'delivery'
    notes: str | None = None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post('/taz-checkout')
def taz_checkout(payload: TazCheckoutIn, db: Session = Depends(get_db)):
    """Check TAZ balance; return approval or Morning top-up link."""
    cust_phone = _clean_phone(payload.customer_phone)
    biz_phone  = _clean_phone(payload.business_phone)
    total      = Decimal(str(payload.total))

    # 1. Find and verify business — try multiple phone formats
    raw_biz = payload.business_phone
    alt_972 = None
    if biz_phone.startswith("972"):
        alt_972 = "0" + biz_phone[3:]
    candidates = list({biz_phone, raw_biz, alt_972} - {None, ""})
    business = db.query(Business).filter(Business.phone.in_(candidates)).first()
    if not business:
        # Regex fallback: match by digits only
        from sqlalchemy import func
        digits = re.sub(r"\D", "", raw_biz)
        business = (
            db.query(Business)
            .filter(func.regexp_replace(Business.phone, "[^0-9]", "", "g") == digits)
            .first()
        )
    if not business:
        return {"approved": False, "reason": "business_not_found",
                "message": "העסק לא נמצא במערכת TAZO"}

    if not _is_biz_verified(business):
        # Notify business via WhatsApp that they have a pending order
        _notify_unverified_business(business)
        return {
            'approved': False,
            'reason': 'business_not_verified',
            'message': f'העסק {business.name} עדיין לא אומת ב-TAZO. שלחנו להם הודעה.',
            'business_name': business.name,
        }

    # 2. Get or create customer wallet
    wallet_rec = _get_or_create_wallet(db, cust_phone)

    # 3. Check vault balance
    balance = vault.get_balance(wallet_rec.wallet_id) or Decimal('0')

    if balance >= total:
        return {
            'approved': True,
            'balance': float(balance),
            'wallet_id': wallet_rec.wallet_id,
            'total': float(total),
            'business_verified': True,
        }

    # 4. Insufficient — generate Morning top-up link
    shortfall = total - balance
    ref = f'{cust_phone}-{uuid.uuid4().hex[:8]}'
    # Store pending ref so webhook can complete the order
    wallet_rec.pending_order_ref = json.dumps({
        'ref': ref,
        'business_phone': biz_phone,
        'items': payload.items,
        'total': float(total),
        'order_type': payload.order_type,
        'notes': payload.notes,
        'customer_name': payload.customer_name,
    })
    db.commit()

    topup_url = _create_morning_topup_link(cust_phone, payload.customer_name or '', shortfall, ref)

    return {
        'approved': False,
        'reason': 'insufficient_balance',
        'balance': float(balance),
        'total': float(total),
        'amount_needed': float(shortfall),
        'needs_topup': True,
        'topup_url': topup_url,
        'message': f'יתרת TAZ לא מספיקה. נדרש לטעון {float(shortfall):.0f} ₪ נוספים.',
    }


@router.post('/taz-debit')
def taz_debit(payload: TazDebitIn, db: Session = Depends(get_db)):
    """Escrow-lock TAZ and forward order to tazo-sync. Called after balance confirmed."""
    cust_phone = _clean_phone(payload.customer_phone)
    amount     = Decimal(str(payload.amount))

    wallet_rec = db.query(CustomerTazWallet).filter(CustomerTazWallet.phone == cust_phone).first()
    if not wallet_rec:
        return {'ok': False, 'error': 'wallet_not_found'}

    result = vault.escrow_lock(wallet_rec.wallet_id, payload.order_id, amount)
    if not result:
        return {'ok': False, 'error': 'escrow_lock_failed'}

    escrow_tx_id = result.get('transaction_id', result.get('vault_tx_id', ''))

    # ── Forward to tazo-sync ──────────────────────────────────────────────────
    try:
        _sync_url = os.environ.get('TAZO_SYNC_URL', 'https://tazo-sync.com') + '/api/orders'
        _sync_key = os.environ.get('TAZO_SYNC_INTERNAL_KEY', '')
        import httpx as _http
        _http.post(
            _sync_url,
            json={
                'businessName':     payload.business_name or payload.business_phone,
                'need':             ', '.join(it.get('name','') for it in (payload.items or []) if isinstance(it, dict)) or 'הזמנת TAZ',
                'businessPhone':    payload.business_phone,
                'customer_phone':   cust_phone,
                'customer_name':    payload.customer_name,
                'items':            payload.items or [],
                'total':            float(amount),
                'amount':           float(amount),
                'order_type':       payload.order_type,
                'notes':            payload.notes,
                'taz_order_id':     payload.order_id,
                'payment_method':   'TAZ',
                'vaultEscrowTxId':  escrow_tx_id,
            },
            headers={'Authorization': f'Bearer {_sync_key}'},
            timeout=10,
        )
    except Exception as _e:
        logger.warning('[TazDebit] tazo-sync forward failed: %s', _e)
    # ─────────────────────────────────────────────────────────────────────────

    return {'ok': True, 'escrow_tx_id': escrow_tx_id, 'amount': float(amount)}


# ── internal helpers ──────────────────────────────────────────────────────────

def _notify_unverified_business(business: Business) -> None:
    """Send WhatsApp to unverified business about pending order."""
    phone = _clean_phone(business.phone or '')
    if not phone:
        return
    msg = (
        f'שלום {business.name}!\n\n'
        f'יש לקוח שמנסה להזמין דרך TAZO אבל העסק שלך עדיין לא אומת.\n'
        f'להשלמת האימות והתחלת קבלת הזמנות: https://tazo-web.com\n\n'
        f'TAZO — מערכת ניהול עסקים חכמה'
    )
    try:
        import httpx as _h
        _h.post(
            'http://sitenest-evolution:8080/message/sendText/tazo-main',
            json={'number': phone, 'text': msg},
            headers={'apikey': 'tazo-evo-key'},
            timeout=5,
        )
    except Exception:
        pass
