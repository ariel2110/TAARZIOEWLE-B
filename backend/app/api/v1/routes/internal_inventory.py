"""
internal_inventory.py
─────────────────────
Receives inventory/product updates from Tazo-Sync and triggers
a site rebuild for the relevant business.

Auth: X-Internal-Key header must match settings.tazo_sync_internal_key
      (same key as TAZO_SYNC_INTERNAL_KEY in .env)

POST /internal/inventory/sync
  Body: {
    "items": [{"name": "מרגריטה", "available": true, "price": 45}, ...]
    "place_id": "ChIJ..." (optional — to identify which business)
    "business_phone": "0521234567" (optional fallback)
  }

POST /internal/site-image
  Body: {
    "image_base64": "...",
    "image_mime": "image/jpeg",
    "field": "hero",           # hero | background (same effect — updates photo_url)
    "primary_color": "#dc2626", # optional hex color for site theme
    "place_id": "ChIJ...",
    "business_phone": "03-629-9696"
  }
  → Saves the image to /static/uploads/ and updates demo_site.photo_url
  → Triggers background rebuild of the site HTML
"""
from __future__ import annotations

import base64
import json
import logging
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal-inventory"])

_STATIC_UPLOADS = Path(__file__).resolve().parents[3] / "static_sites" / "uploads"


# ── Auth ──────────────────────────────────────────────────────────────────────

def _verify_sync_key(x_internal_key: str | None = Header(default=None)) -> None:
    expected = settings.tazo_sync_internal_key
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Inventory sync not configured")
    if x_internal_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid internal key")


# ── Shared lookup ─────────────────────────────────────────────────────────────

def _find_biz(db: Session, place_id: str | None, phone: str | None):
    from app.models.business import Business
    from sqlalchemy import func
    if place_id:
        biz = db.query(Business).filter(Business.google_place_id == place_id).first()
        if biz:
            return biz
    if phone:
        digits = re.sub(r"\D", "", phone)
        if digits.startswith("0") and len(digits) == 10:
            digits = "972" + digits[1:]
        suffix = digits[-9:]
        # strip non-digits from stored phone and compare suffix
        biz = db.query(Business).filter(
            func.regexp_replace(Business.phone, r"[^\d]", "", "g").like(f"%{suffix}")
        ).first()
        if biz:
            return biz
    return None


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductItem(BaseModel):
    name: str
    available: bool = True
    price: float | None = None
    description: str | None = None
    emoji: str | None = None


class InventorySyncRequest(BaseModel):
    items: list[ProductItem]
    place_id: str | None = None
    business_phone: str | None = None


class SiteImageRequest(BaseModel):
    image_base64: str
    image_mime: str = "image/jpeg"
    field: str = "hero"               # hero | background (both update photo_url)
    primary_color: str | None = None   # e.g. "#dc2626"
    place_id: str | None = None
    business_phone: str | None = None


# ── Background helpers ────────────────────────────────────────────────────────

def _rebuild_site_for_business(business_id: int, items: list[dict]) -> None:
    """Persist synced products and rebuild the draft site when one exists."""
    try:
        from app.db.session import SessionLocal
        from app.models.business import Business
        from app.models.demo_site import DemoSite
        from app.models.draft_site import DraftSite
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db: Session = SessionLocal()
        try:
            biz = db.query(Business).filter(Business.id == business_id).first()
            if not biz:
                logger.warning("[inventory-sync] business %s not found for rebuild", business_id)
                return

            demo_sites = db.query(DemoSite).filter(DemoSite.business_id == business_id).all()
            if demo_sites:
                payload = json.dumps(items, ensure_ascii=False)
                for demo in demo_sites:
                    demo.menu_items_json = payload
                db.commit()
                logger.info("[inventory-sync] updated %d demo site(s) for business %s",
                            len(demo_sites), business_id)

            draft = db.query(DraftSite).filter(DraftSite.business_id == business_id).order_by(DraftSite.id.desc()).first()
            if draft:
                svc = DraftSiteService()
                svc.generate_preview(db, draft.id)
                logger.info("[inventory-sync] rebuilt site for business %s (draft %s)", business_id, draft.id)
            elif not demo_sites:
                logger.info("[inventory-sync] no draft or demo site for business %s — skipping rebuild", business_id)
        finally:
            db.close()
    except Exception as exc:
        logger.warning("[inventory-sync] rebuild failed for business %s: %s", business_id, exc)


def _rebuild_after_image(business_id: int, image_url: str, primary_color: str | None) -> None:
    """After saving an image: update demo_sites photo_url and rebuild HTML."""
    try:
        from app.db.session import SessionLocal
        from app.models.demo_site import DemoSite
        from app.models.draft_site import DraftSite
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db: Session = SessionLocal()
        try:
            demos = db.query(DemoSite).filter(DemoSite.business_id == business_id).all()
            for demo in demos:
                demo.photo_url = image_url
            if demos:
                db.commit()
                logger.info("[site-image] updated photo_url for %d demo(s) biz=%s", len(demos), business_id)

            draft = db.query(DraftSite).filter(DraftSite.business_id == business_id).order_by(DraftSite.id.desc()).first()
            if draft:
                if primary_color:
                    draft.primary_color = primary_color
                    db.commit()
                svc = DraftSiteService()
                svc.generate_preview(db, draft.id)
                logger.info("[site-image] rebuilt draft site for biz=%s", business_id)
        finally:
            db.close()
    except Exception as exc:
        logger.warning("[site-image] rebuild failed for biz %s: %s", business_id, exc)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/inventory/sync")
async def inventory_sync(
    payload: InventorySyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_sync_key),
) -> dict[str, Any]:
    """Receive product availability update from Tazo-Sync and queue a site rebuild."""
    biz = _find_biz(db, payload.place_id, payload.business_phone)

    if not biz:
        logger.info("[inventory-sync] business not found (place_id=%s phone=%s) — queued 0 rebuilds",
                    payload.place_id, payload.business_phone)
        return {"ok": True, "rebuilt": False, "reason": "business not found"}

    items_dicts = [item.model_dump(exclude_none=True) for item in payload.items]
    background_tasks.add_task(_rebuild_site_for_business, biz.id, items_dicts)

    logger.info("[inventory-sync] queued rebuild for business %s (%s), %d items",
                biz.id, biz.name, len(payload.items))
    return {"ok": True, "rebuilt": True, "business_id": biz.id, "business_name": biz.name, "items_count": len(payload.items)}


@router.post("/site-image")
async def update_site_image(
    payload: SiteImageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_sync_key),
) -> dict[str, Any]:
    """
    Receive a base64-encoded image from Tazo-Sync merchant bot,
    save it as a static file, update the demo site hero image, and rebuild.
    """
    biz = _find_biz(db, payload.place_id, payload.business_phone)

    if not biz:
        logger.info("[site-image] business not found (place_id=%s phone=%s)",
                    payload.place_id, payload.business_phone)
        return {"ok": False, "reason": "business not found"}

    # Validate MIME and pick extension
    allowed_mimes = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = allowed_mimes.get(payload.image_mime, "jpg")

    # Decode and save
    try:
        img_bytes = base64.b64decode(payload.image_base64)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid base64 image: {exc}")

    _STATIC_UPLOADS.mkdir(parents=True, exist_ok=True)
    img_path = _STATIC_UPLOADS / f"biz_{biz.id}.{ext}"
    img_path.write_bytes(img_bytes)

    image_url = f"/static/uploads/biz_{biz.id}.{ext}"
    logger.info("[site-image] saved %d bytes → %s for biz %s (%s)",
                len(img_bytes), img_path, biz.id, biz.name)

    background_tasks.add_task(_rebuild_after_image, biz.id, image_url, payload.primary_color)

    return {
        "ok": True,
        "image_url": image_url,
        "business_id": biz.id,
        "business_name": biz.name,
    }
