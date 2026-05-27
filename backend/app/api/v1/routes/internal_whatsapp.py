"""
Internal WhatsApp QR / status / approval endpoints.
Proxies Evolution API so the browser-based QR page can work without
exposing the Evolution API key to the client. Also exposes admin
approval endpoints for queued outreach messages.

Approval routes require a valid admin JWT (same as all other admin routes).
"""
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_admin
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/internal", tags=["internal"])


def _evolution_url() -> str:
    return (settings.evolution_api_url or "http://127.0.0.1:8181").rstrip("/")


def _evolution_key() -> str:
    return settings.evolution_api_key or ""


def _evolution_instance() -> str:
    return settings.evolution_instance or "TAZO-WEB"


def _headers() -> dict:
    return {"apikey": _evolution_key(), "Content-Type": "application/json"}


@router.get("/whatsapp-qr")
async def get_whatsapp_qr():
    """Return current QR code (base64 PNG) for the WhatsApp instance."""
    if not _evolution_key():
        raise HTTPException(503, "Evolution API not configured")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{_evolution_url()}/instance/connect/{_evolution_instance()}",
            headers=_headers(),
        )
    if r.status_code != 200:
        return JSONResponse({"connected": True})  # likely already connected
    data = r.json()
    # data has: base64, code, count  — or {"status":"open"} when connected
    if isinstance(data, dict) and data.get("base64"):
        return JSONResponse({
            "connected": False,
            "base64": data["base64"],
            "code": data.get("code", ""),
            "count": data.get("count", 0),
        })
    return JSONResponse({"connected": True})


@router.get("/whatsapp-status")
async def get_whatsapp_status():
    """Return connection status of the WhatsApp instance."""
    if not _evolution_key():
        return JSONResponse({"status": "not_configured"})
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{_evolution_url()}/instance/fetchInstances?instanceName={_evolution_instance()}",
            headers=_headers(),
        )
    if r.status_code != 200:
        return JSONResponse({"status": "error"})
    data = r.json()
    # v1.x returns {"instance": {..., "status": "..."}}
    # v2.x returns [{"connectionStatus": "..."}]
    if isinstance(data, dict) and "instance" in data:
        status = data["instance"].get("status", "close")
        return JSONResponse({"status": status})
    if isinstance(data, list) and data:
        status = data[0].get("connectionStatus", data[0].get("status", "close"))
        return JSONResponse({"status": status})
    return JSONResponse({"status": "unknown"})


# ── WhatsApp Approval Queue ───────────────────────────────────────────────────

class ApproveBody(BaseModel):
    message: Optional[str] = None  # if provided, sends this edited text instead


@router.get("/pending-messages")
async def pending_messages(_: User = Depends(get_current_admin)):
    """Return all pending WhatsApp messages awaiting approval."""
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    db = SessionLocal()
    try:
        rows = (
            db.query(PublicIntake)
            .filter(PublicIntake.whatsapp_status == "pending")
            .order_by(PublicIntake.id.desc())
            .all()
        )
        return JSONResponse([
            {
                "token": r.token,
                "business_name": r.business_name,
                "phone": r.phone,
                "message": r.whatsapp_pending_message,
                "preview_url": r.generated_preview_url,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ])
    finally:
        db.close()


@router.post("/approve-message/{token}")
async def approve_message(token: str, body: ApproveBody = ApproveBody(), _: User = Depends(get_current_admin)):
    """Approve (and optionally edit) a pending WhatsApp message and send it to the lead."""
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    from app.services.communications.meta_whatsapp_service import MetaWhatsAppService
    db = SessionLocal()
    try:
        intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
        if not intake:
            raise HTTPException(404, "Intake not found")
        if intake.whatsapp_status != "pending":
            raise HTTPException(400, f"Message is not pending (status: {intake.whatsapp_status})")

        final_message = body.message if body.message and body.message.strip() else intake.whatsapp_pending_message
        if not final_message:
            raise HTTPException(400, "No message to send")

        sent = MetaWhatsAppService().send_text(intake.phone, final_message)
        if not sent:
            raise HTTPException(502, "Failed to send via Evolution API")

        intake.whatsapp_status = "sent"
        intake.whatsapp_pending_message = final_message  # save what was actually sent
        db.commit()
        return JSONResponse({"ok": True, "sent_to": intake.phone})
    finally:
        db.close()


@router.post("/reject-message/{token}")
async def reject_message(token: str, _: User = Depends(get_current_admin)):
    """Reject a pending WhatsApp message — will not be sent."""
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    db = SessionLocal()
    try:
        intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
        if not intake:
            raise HTTPException(404, "Intake not found")
        intake.whatsapp_status = "rejected"
        db.commit()
        return JSONResponse({"ok": True, "rejected": token})
    finally:
        db.close()


# ── WhatsApp Connection Management ───────────────────────────────────────────

@router.post("/whatsapp-disconnect")
async def whatsapp_disconnect(_: User = Depends(get_current_admin)):
    """Logout the WhatsApp session (disconnect from phone). Requires QR re-scan after."""
    if not _evolution_key():
        raise HTTPException(503, "Evolution API not configured")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.delete(
            f"{_evolution_url()}/instance/logout/{_evolution_instance()}",
            headers=_headers(),
        )
    if r.status_code in (200, 201):
        return JSONResponse({"ok": True, "message": "Disconnected"})
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    msg = data.get("response", {}).get("message", ["Unknown error"])
    # 400 "not connected" is still a valid "already disconnected" state
    if r.status_code == 400 and "not connected" in str(msg).lower():
        return JSONResponse({"ok": True, "message": "Already disconnected"})
    raise HTTPException(r.status_code, detail=str(msg))


@router.post("/whatsapp-reconnect")
async def whatsapp_reconnect(_: User = Depends(get_current_admin)):
    """Trigger a new QR code / pairing code so the instance can reconnect."""
    if not _evolution_key():
        raise HTTPException(503, "Evolution API not configured")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{_evolution_url()}/instance/connect/{_evolution_instance()}",
            headers=_headers(),
        )
    if r.status_code != 200:
        raise HTTPException(r.status_code, detail="Evolution API error")
    data = r.json()
    if isinstance(data, dict) and data.get("base64"):
        return JSONResponse({
            "connected": False,
            "base64": data["base64"],
            "code": data.get("code", ""),
            "count": data.get("count", 0),
        })
    return JSONResponse({"connected": True})
