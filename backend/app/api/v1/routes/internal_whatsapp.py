"""
Internal WhatsApp QR / status endpoints.
Proxies Evolution API so the browser-based QR page can work without
exposing the Evolution API key to the client.

Accessible only from localhost (127.0.0.1) — enforced via nginx or
trusted-host checks. No auth required because the page is served from
the same origin and the routes are intentionally short-lived for setup.
"""
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

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
