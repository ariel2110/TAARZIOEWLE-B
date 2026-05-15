"""Public endpoint for logging food orders placed via demo/draft sites.

Orders are:
  1. Sent via WhatsApp to business owner
  2. Forwarded to TAZO-SYNC (tazo-sync.com) for order management
  3. Admin notification sent
"""
from __future__ import annotations

import threading
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter(prefix='/public', tags=['public-orders'])

_WA_BASE     = 'http://sitenest-evolution:8080'
_WA_INSTANCE = 'tazo-main'
_WA_KEY      = 'tazo-evo-key'
_ADMIN_PHONE = '972546363350'
_SYNC_URL    = 'https://tazo-sync.com/api/v1/orders'
_SYNC_KEY    = 'tazo-sync-internal'


class SiteOrderIn(BaseModel):
    business_name:  str | None = None
    business_phone: str | None = None
    customer_name:  str | None = None
    customer_phone: str | None = None
    items:  list | None = None
    total:  float | None = None
    order_type: str | None = None   # 'delivery' or 'pickup'
    notes:  str | None = None


def _send_wa(phone: str, text: str) -> None:
    try:
        httpx.post(
            f'{_WA_BASE}/message/sendText/{_WA_INSTANCE}',
            json={'number': phone, 'text': text},
            headers={'apikey': _WA_KEY},
            timeout=8,
        )
    except Exception:
        pass


def _forward_to_sync(payload: dict) -> None:
    """Forward order to TAZO-SYNC in a background thread."""
    try:
        httpx.post(
            _SYNC_URL,
            json=payload,
            headers={'Authorization': f'Bearer {_SYNC_KEY}', 'Content-Type': 'application/json'},
            timeout=10,
        )
    except Exception:
        pass


def _clean_phone(raw: str) -> str:
    import re
    p = re.sub(r'\D', '', raw or '')
    if p.startswith('0') and len(p) == 10:
        p = '972' + p[1:]
    return p


@router.post('/site-order')
def create_site_order(order: SiteOrderIn, db: Session = Depends(get_db)):
    """Receive an order from a demo/draft food site."""
    biz_name   = order.business_name or 'עסק'
    customer   = order.customer_name or 'לקוח'
    cust_phone = order.customer_phone or '-'
    order_type_label = 'משלוח' if order.order_type == 'delivery' else 'איסוף עצמי'
    total_str  = f'\u20aa{order.total:.0f}' if order.total else ''

    # Build items summary
    items_text = ''
    if order.items:
        lines = []
        for it in order.items:
            name  = it.get('name', '')  if isinstance(it, dict) else str(it)
            qty   = it.get('qty',  1)   if isinstance(it, dict) else 1
            price = it.get('price', 0)  if isinstance(it, dict) else 0
            lines.append(f'\u2022 {name} x{qty} \u2014 \u20aa{price}')
        items_text = '\n'.join(lines)

    # --- WhatsApp to business owner ---
    biz_clean = _clean_phone(order.business_phone or '')
    if biz_clean:
        biz_msg = (
            f'\U0001f355 \u05d4\u05d6\u05de\u05e0\u05d4 \u05d7\u05d3\u05e9\u05d4 \u05de-TAZO!\n\n'
            f'\u05dc\u05e7\u05d5\u05d7: {customer}\n'
            f'\u05d8\u05dc\u05e4\u05d5\u05df: {cust_phone}\n'
            f'\u05e1\u05d5\u05d2: {order_type_label}\n'
        )
        if items_text:
            biz_msg += f'\n\u05e4\u05e8\u05d9\u05d8\u05d9\u05dd:\n{items_text}\n'
        if total_str:
            biz_msg += f'\n\u05e1\u05d4"\u05db: {total_str}'
        if order.notes:
            biz_msg += f'\n\u05d4\u05e2\u05e8\u05d5\u05ea: {order.notes}'
        _send_wa(biz_clean, biz_msg)

    # --- Admin notification ---
    admin_msg = (
        f'\U0001f4e6 \u05d4\u05d6\u05de\u05e0\u05d4: {biz_name}\n'
        f'\u05dc\u05e7\u05d5\u05d7: {customer} ({cust_phone})\n'
        f'\u05e1\u05d5\u05d2: {order_type_label} {total_str}'
    )
    _send_wa(_ADMIN_PHONE, admin_msg)

    # --- Forward to TAZO-SYNC (background, non-blocking) ---
    sync_payload = {
        'source': 'tazo-web',
        'business_name':  biz_name,
        'business_phone': biz_clean or None,
        'customer_name':  customer,
        'customer_phone': cust_phone,
        'items':     order.items or [],
        'total':     order.total or 0,
        'order_type': order.order_type,
        'notes':     order.notes or '',
        'creditOffer': 0,   # skip auth requirement
    }
    t = threading.Thread(target=_forward_to_sync, args=(sync_payload,), daemon=True)
    t.start()

    return {'ok': True, 'order_received': True}
