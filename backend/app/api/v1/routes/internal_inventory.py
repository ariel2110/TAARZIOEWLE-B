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
  → Updates product availability on the matching DraftSite / DemoSite
  → Triggers background rebuild of the site HTML
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal-inventory"])


# ── Auth ──────────────────────────────────────────────────────────────────────

def _verify_sync_key(x_internal_key: str | None = Header(default=None)) -> None:
    expected = settings.tazo_sync_internal_key
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Inventory sync not configured")
    if x_internal_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid internal key")


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


# ── Background rebuild ────────────────────────────────────────────────────────

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


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/inventory/sync")
async def inventory_sync(
    payload: InventorySyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_sync_key),
) -> dict[str, Any]:
    """
    Receive product availability update from Tazo-Sync.
    Finds the matching business and queues a site rebuild.
    """
    from app.models.business import Business

    biz = None

    # Try by place_id first
    if payload.place_id:
        biz = db.query(Business).filter(Business.google_place_id == payload.place_id).first()

    # Fallback: by phone
    if not biz and payload.business_phone:
        phone_clean = payload.business_phone.replace(" ", "").replace("-", "").replace("+", "")
        if phone_clean.startswith("0") and len(phone_clean) == 10:
            phone_clean = "972" + phone_clean[1:]
        biz = db.query(Business).filter(
            Business.phone.like(f"%{phone_clean[-9:]}")
        ).first()

    if not biz:
        # Non-fatal — log and return ok (sync is best-effort)
        logger.info("[inventory-sync] business not found (place_id=%s phone=%s) — queued 0 rebuilds",
                    payload.place_id, payload.business_phone)
        return {"ok": True, "rebuilt": False, "reason": "business not found"}

    items_dicts = [item.model_dump(exclude_none=True) for item in payload.items]
    background_tasks.add_task(_rebuild_site_for_business, biz.id, items_dicts)

    logger.info("[inventory-sync] queued rebuild for business %s (%s), %d items",
                biz.id, biz.name, len(payload.items))
    return {"ok": True, "rebuilt": True, "business_id": biz.id, "business_name": biz.name, "items_count": len(payload.items)}
