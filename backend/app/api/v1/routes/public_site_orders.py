"""Public endpoint for logging food orders placed via demo/draft sites.

Orders are:
  1. Sent via WhatsApp to business owner
  2. Forwarded to TAZO-SYNC (tazo-sync.com) for order management
  3. Admin notification sent
"""
from __future__ import annotations

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
# tazo-sync nginx: /api/ -> backend:3000/ (strips /api prefix)
# So /api/orders maps to backend /orders route
_SYNC_URL    = 'https://tazo-sync.com/api/orders'
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


def _forward_to_sync(payload: dict) -> dict:
    """Forward order to TAZO-SYNC and return parsed response (with deliveryCode)."""
    try:
        resp = httpx.post(
            _SYNC_URL,
            json=payload,
            headers={'Authorization': f'Bearer {_SYNC_KEY}', 'Content-Type': 'application/json'},
            timeout=12,
        )
        if resp.status_code < 300:
            return resp.json()
    except Exception:
        pass
    return {}


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
        'businessName':  biz_name,       # tazo-sync requires businessName (camelCase)
        'business_phone': biz_clean or None,
        'buyerPhone':    cust_phone,     # tazo-sync field for customer phone
        'customer_name':  customer,
        'customer_phone': cust_phone,
        'need':          ', '.join(i.get('name','') for i in (order.items or []) if i.get('name')) or 'הזמנה',
        'items':     order.items or [],
        'total':     order.total or 0,
        'order_type': order.order_type,
        'notes':     order.notes or '',
        'creditOffer': 0,   # skip auth requirement
        'isShadowOrder': True,           # triggers merchant WhatsApp notification
        'shadowMerchantPhone': biz_clean or None,
    }
    # Forward to TAZO-SYNC synchronously to capture deliveryCode
    sync_resp   = _forward_to_sync(sync_payload)
    # tazo-sync assigns deliveryCode at dispatch time (when business accepts),
    # but we get the order _id now — build a pre-tracking URL with orderId
    order_id      = str(sync_resp.get('_id') or sync_resp.get('id') or '')
    delivery_code = sync_resp.get('deliveryCode') or None
    if delivery_code:
        tracking_url = f'https://tazo-sync.com/track/{delivery_code}'
    elif order_id:
        # Pre-tracking link using order ID — will show CREATED status
        tracking_url = f'https://tazo-sync.com/track?order={order_id}'
    else:
        tracking_url = None

    return {
        'ok': True,
        'order_received': True,
        'deliveryCode': delivery_code,
        'trackingUrl': tracking_url,
    }
