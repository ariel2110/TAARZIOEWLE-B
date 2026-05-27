"""Admin WhatsApp management — connect, disconnect, QR, pending messages.

All endpoints require a valid admin JWT (Bearer token).
Proxies to the self-hosted Evolution API instance.
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_admin
from app.core.config import settings

router = APIRouter(
    prefix='/admin/whatsapp',
    tags=['admin-whatsapp'],
    dependencies=[Depends(get_current_admin)],
)

_EVO_URL = lambda: (settings.evolution_api_url or 'http://127.0.0.1:8181').rstrip('/')
_EVO_KEY = lambda: settings.evolution_api_key or ''
_EVO_INST = lambda: settings.evolution_instance or 'TAZO-WEB'
_HEADERS = lambda: {'apikey': _EVO_KEY(), 'Content-Type': 'application/json'}
_TIMEOUT = 15


def _evo_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=_TIMEOUT)


@router.get('/status')
async def wa_status():
    """Return WhatsApp connection status: open | connecting | close."""
    async with _evo_client() as client:
        r = await client.get(
            f'{_EVO_URL()}/instance/fetchInstances?instanceName={_EVO_INST()}',
            headers=_HEADERS(),
        )
    if r.status_code != 200:
        return JSONResponse({'status': 'error'})
    data = r.json()
    if isinstance(data, dict) and 'instance' in data:
        inst = data['instance']
        return JSONResponse({
            'status': inst.get('status', 'close'),
            'owner': inst.get('owner', ''),
            'profile_name': inst.get('profileName', ''),
            'profile_picture': inst.get('profilePictureUrl', ''),
        })
    if isinstance(data, list) and data:
        return JSONResponse({'status': data[0].get('connectionStatus', 'close')})
    return JSONResponse({'status': 'unknown'})


@router.get('/qr')
async def wa_qr():
    """Get current QR code (base64 PNG) to reconnect. Returns {connected:true} if already open."""
    async with _evo_client() as client:
        r = await client.get(
            f'{_EVO_URL()}/instance/connect/{_EVO_INST()}',
            headers=_HEADERS(),
        )
    if r.status_code != 200:
        return JSONResponse({'connected': True})
    data = r.json()
    if isinstance(data, dict) and data.get('base64'):
        return JSONResponse({
            'connected': False,
            'base64': data['base64'],
            'code': data.get('code', ''),
            'count': data.get('count', 0),
        })
    return JSONResponse({'connected': True})


@router.post('/disconnect')
async def wa_disconnect():
    """Logout the WhatsApp session. After this a new QR scan will be needed."""
    async with _evo_client() as client:
        r = await client.delete(
            f'{_EVO_URL()}/instance/logout/{_EVO_INST()}',
            headers=_HEADERS(),
        )
    if r.status_code in (200, 201):
        return JSONResponse({'ok': True, 'message': 'Disconnected'})
    try:
        data = r.json()
        msg = str(data.get('response', {}).get('message', 'Unknown'))
    except Exception:
        msg = r.text[:200]
    if r.status_code == 400 and 'not connected' in msg.lower():
        return JSONResponse({'ok': True, 'message': 'Already disconnected'})
    raise HTTPException(status_code=r.status_code, detail=msg)


@router.post('/reconnect')
async def wa_reconnect():
    """Trigger reconnection — returns a fresh QR code or {connected:true} if already open."""
    async with _evo_client() as client:
        r = await client.get(
            f'{_EVO_URL()}/instance/connect/{_EVO_INST()}',
            headers=_HEADERS(),
        )
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail='Evolution API error')
    data = r.json()
    if isinstance(data, dict) and data.get('base64'):
        return JSONResponse({
            'connected': False,
            'base64': data['base64'],
            'code': data.get('code', ''),
            'count': data.get('count', 0),
        })
    return JSONResponse({'connected': True})


# ── Pending message approval queue ───────────────────────────────────────────

@router.get('/pending-messages')
async def pending_messages():
    """Return all pending WhatsApp messages awaiting admin approval."""
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    db = SessionLocal()
    try:
        rows = (
            db.query(PublicIntake)
            .filter(PublicIntake.whatsapp_status == 'pending')
            .order_by(PublicIntake.id.desc())
            .all()
        )
        return JSONResponse([
            {
                'token': r.token,
                'business_name': r.business_name,
                'phone': r.phone,
                'message': r.whatsapp_pending_message,
                'preview_url': r.generated_preview_url,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ])
    finally:
        db.close()


class ApproveBody(BaseModel):
    message: Optional[str] = None


@router.post('/approve-message/{token}')
async def approve_message(token: str, body: ApproveBody = ApproveBody()):
    """Approve (and optionally edit) a pending WhatsApp message and send it to the lead."""
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    from app.services.communications.meta_whatsapp_service import MetaWhatsAppService
    db = SessionLocal()
    try:
        intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
        if not intake:
            raise HTTPException(404, 'Intake not found')
        if intake.whatsapp_status != 'pending':
            raise HTTPException(400, f'Message not pending (status: {intake.whatsapp_status})')
        final_msg = (body.message or '').strip() or intake.whatsapp_pending_message
        if not final_msg:
            raise HTTPException(400, 'No message to send')
        sent = MetaWhatsAppService().send_text(intake.phone, final_msg)
        if not sent:
            raise HTTPException(502, 'Failed to send via Evolution API')
        intake.whatsapp_status = 'sent'
        intake.whatsapp_pending_message = final_msg
        db.commit()
        return JSONResponse({'ok': True, 'sent_to': intake.phone})
    finally:
        db.close()


@router.post('/reject-message/{token}')
async def reject_message(token: str):
    """Discard a pending WhatsApp message — it will not be sent."""
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    db = SessionLocal()
    try:
        intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
        if not intake:
            raise HTTPException(404, 'Intake not found')
        intake.whatsapp_status = 'rejected'
        db.commit()
        return JSONResponse({'ok': True, 'rejected': token})
    finally:
        db.close()
