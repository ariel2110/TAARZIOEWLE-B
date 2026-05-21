"""Cross-app SSO — verify a single-use JWT issued by tazo-go.

Flow:
  1. Passenger in tazo-go mall clicks a tazo-web link.
  2. tazo-go frontend calls POST /api/auth/cross-app-token → receives {token, redirect_url}.
  3. Browser is redirected to https://tazo-web.com/?cross_auth=TOKEN.
  4. tazo-web Marketplace mounts and calls GET /api/v1/public/cross-auth/verify?token=TOKEN.
  5. This endpoint calls tazo-go's consume endpoint to single-use-invalidate the token.
  6. Returns {phone, role, ok: true} so the frontend can pre-fill the intake form.
"""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/cross-auth", tags=["cross-auth"])


@router.get("/verify")
async def verify_cross_auth(token: str = Query(..., description="Cross-app JWT issued by tazo-go")) -> dict:
    """Verify and consume a cross-app token issued by tazo-go.

    Calls tazo-go's internal consume endpoint so the token is single-use.
    Returns the passenger's phone number and role on success.
    """
    if not settings.cross_app_secret:
        raise HTTPException(status_code=503, detail="Cross-app SSO not configured")

    consume_url = f"{settings.tazo_go_url}/api/auth/cross-app-token/consume"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                consume_url,
                json={"token": token},
                headers={
                    "X-Cross-App-Secret": settings.cross_app_secret,
                    "Content-Type": "application/json",
                },
            )
    except httpx.RequestError as exc:
        logger.warning("cross-auth: could not reach tazo-go: %s", exc)
        raise HTTPException(status_code=503, detail="Could not reach tazo-go server")

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Token invalid, expired or already used")
    if not resp.is_success:
        logger.warning("cross-auth: tazo-go returned %s: %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=502, detail="tazo-go returned unexpected error")

    data = resp.json()
    return {
        "ok": True,
        "phone": data.get("phone", ""),
        "role": data.get("role", "passenger"),
    }
