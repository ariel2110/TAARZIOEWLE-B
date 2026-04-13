"""
Internal WhatsApp QR / status / approval endpoints.
Proxies Evolution API so the browser-based QR page can work without
exposing the Evolution API key to the client. Also exposes admin
approval endpoints for queued outreach messages.

Approval routes require ?key=<ADMIN_DEV_TOKEN> query parameter.
"""
import httpx
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings

router = APIRouter(prefix="/internal", tags=["internal"])

EVOLUTION_URL = (settings.evolution_api_url or "http://127.0.0.1:8181").rstrip("/")
EVOLUTION_KEY = settings.evolution_api_key or ""
EVOLUTION_INSTANCE = settings.evolution_instance or "sitenest"


def _headers() -> dict:
    return {"apikey": EVOLUTION_KEY, "Content-Type": "application/json"}


@router.get("/whatsapp-qr")
async def get_whatsapp_qr():
    """Return current QR code (base64 PNG) for the WhatsApp instance."""
    if not EVOLUTION_KEY:
        raise HTTPException(503, "Evolution API not configured")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{EVOLUTION_URL}/instance/connect/{EVOLUTION_INSTANCE}",
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
    if not EVOLUTION_KEY:
        return JSONResponse({"status": "not_configured"})
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{EVOLUTION_URL}/instance/fetchInstances?instanceName={EVOLUTION_INSTANCE}",
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


def _require_admin(key: str) -> None:
    """Raise 403 if the provided key does not match the admin dev token."""
    if key != settings.admin_dev_token:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/pending-messages")
async def pending_messages(key: str = Query(...)):
    """Return all pending WhatsApp messages awaiting approval."""
    _require_admin(key)
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
async def approve_message(token: str, body: ApproveBody = ApproveBody(), key: str = Query(...)):
    """Approve (and optionally edit) a pending WhatsApp message and send it to the lead."""
    _require_admin(key)
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
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

        sent = EvolutionWhatsAppService().send_text(intake.phone, final_message)
        if not sent:
            raise HTTPException(502, "Failed to send via Evolution API")

        intake.whatsapp_status = "sent"
        intake.whatsapp_pending_message = final_message  # save what was actually sent
        db.commit()
        return JSONResponse({"ok": True, "sent_to": intake.phone})
    finally:
        db.close()


@router.post("/reject-message/{token}")
async def reject_message(token: str, key: str = Query(...)):
    """Reject a pending WhatsApp message — will not be sent."""
    _require_admin(key)
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
