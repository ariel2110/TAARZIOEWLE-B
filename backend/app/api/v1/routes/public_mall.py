"""Public Mall API — TAZO Mall v3 — Nearby Search + Build-from-Place."""
from __future__ import annotations
import logging, re, math
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.business import Business
from app.models.demo_site import DemoSite
from app.models.draft_site import DraftSite

logger = logging.getLogger(__name__)

# ── tazo-sync cross-server notification ──────────────────────────────────────
async def _notify_tazo_sync(place_id: str, name: str, phone: str, address: str,
                             city: str, category: str, rating: float,
                             lat: float | None, lng: float | None,
                             photo_url: str = "", website: str = "",
                             description: str = "", slug: str = "") -> None:
    """Notify tazo-sync to create/update a shadow Business panel."""
    import os
    sync_url  = os.environ.get("TAZO_SYNC_URL", "http://145.223.81.124:3000")
    sync_key  = os.environ.get("TAZO_SYNC_INTERNAL_KEY", "")
    if not sync_key:
        return
    payload = {
        "placeId":      place_id,
        "name":         name,
        "phone":        phone or "",
        "address":      address or "",
        "city":         city or "",
        "category":     category or "business",
        "rating":       rating or 0,
        "lat":          lat,
        "lng":          lng,
        "photoUrl":     photo_url or "",
        "website":      website or "",
        "description":  description or "",
        "tazo_web_slug": slug or "",
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(
                f"{sync_url}/internal/sync-shadow",
                json=payload,
                headers={"x-internal-key": sync_key, "Content-Type": "application/json"},
            )
            logger.info(f"[tazo-sync] shadow for {name}: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        logger.warning(f"[tazo-sync] notify failed for {name}: {e}")


router = APIRouter(prefix="/public/mall", tags=["public-mall"])

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food":["פיצה","מסעדה","גריל","שוורמה","פלאפל","סושי","המבורגר","אוכל"],
    "cafe":["קפה","קפיטריה","מאפיה","בייגלה","עוגות","מאפה"],
    "beauty":["מספרה","ספרות","יופי","ציפורניים","ספא","כלה","מניקור"],
    "health":["פיזיותרפיה","יוגה","פילאטיס","כושר","רפואה","קליניקה"],
    "repairs":["שיפוץ","שיפוצים","צביעה","ריצוף","גבס","נגרות","אחזקה"],
    "electric":["חשמלאי","שרברב","מזגן","חשמל","אינסטלציה"],
    "vehicles":["מוסך","מכונאות","צמיגים","רכב","גרר"],
    "garden":["גנן","גינון","עיצוב גינה","נוף"],
    "cleaning":["ניקיון","מנקה","שטיחים","חלונות","כביסה"],
    "pets":["וטרינר","גן כלבים","חיות מחמד","אילוף","כלב","חתול"],
    "education":["גן ילדים","שיעורים פרטיים","קורסים","חינוך","אנגלית"],
    "events":["אולם אירועים","צלמים","קייטרינג","בידור","אירוע","חתונה"],
}

CATEGORY_SEARCH_TERMS: dict[str, list[str]] = {
    "food": ["מסעדה","פיצה","שוורמה","גריל","סושי","המבורגר","פלאפל"],
    "cafe": ["בית קפה","קפה","מאפייה","עוגות"],
    "beauty": ["מספרה","מכון יופי","ספא","ציפורניים","מניקור","פדיקור"],
    "health": ["פיזיותרפיה","יוגה","פילאטיס","כושר","קליניקה"],
    "repairs": ["שיפוצניק","שיפוצים","נגר","צביעה","ריצוף"],
    "electric": ["חשמלאי","שרברב","אינסטלציה","מזגן"],
    "vehicles": ["מוסך","מכונאות","צמיגים","גרר"],
    "garden": ["גנן","גינון","עיצוב גינה"],
    "cleaning": ["ניקיון","מנקה","שטיחים"],
    "pets": ["וטרינר","גן כלבים","אילוף"],
    "education": ["גן ילדים","שיעורים פרטיים","קורסים"],
    "events": ["אולם אירועים","קייטרינג","צלם"],
}

PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
DETAIL_FIELDS = "name,formatted_address,formatted_phone_number,rating,user_ratings_total,place_id,geometry,types,vicinity"


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in km between two lat/lng points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _matches(text: str | None, terms: list[str]) -> bool:
    if not text: return False
    t = text.lower()
    return any(kw.lower() in t for kw in terms)

def _demo_to_dict(d: DemoSite) -> dict:
    return {"id": d.id, "name": d.business_name, "city": d.city, "phone": d.phone,
            "rating": d.rating, "reviews_count": getattr(d, "reviews_count", None),
            "tagline": d.tagline, "status": "active", "subdomain": d.slug,
            "place_id": getattr(d, "place_id", None),
            "photo_url": getattr(d, "photo_url", None)}

def _biz_to_dict(biz: Business, status: str) -> dict:
    return {"id": biz.id, "name": biz.name, "city": biz.city, "phone": biz.phone,
            "rating": None, "reviews_count": None, "tagline": None, "status": status, "subdomain": None}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    demos = db.query(DemoSite).all()
    counts = {k: 0 for k in CATEGORY_KEYWORDS}
    for d in demos:
        for cat_id, terms in CATEGORY_KEYWORDS.items():
            if _matches(d.category, terms) or _matches(d.business_name, terms):
                counts[cat_id] += 1; break
    return {"categories": [{"id": k, "count": v} for k, v in counts.items()]}


@router.get("/businesses")
def list_businesses(category: str = Query(..., min_length=1),
                    city: Optional[str] = Query(None), q: Optional[str] = Query(None),
                    limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    terms = CATEGORY_KEYWORDS.get(category, [category])
    result: list[dict] = []
    for d in db.query(DemoSite).filter(DemoSite.slug.isnot(None)).all():
        if not (_matches(d.category, terms) or _matches(d.business_name, terms)): continue
        if city and city not in (d.city or ""): continue
        if q and q.lower() not in (d.business_name or "").lower() and q.lower() not in (d.city or "").lower(): continue
        result.append(_demo_to_dict(d))
    draft_ids = {r[0] for r in db.query(DraftSite.business_id).all()}
    for biz in db.query(Business).filter(Business.status != "deleted").all():
        if not (_matches(biz.category, terms) or _matches(biz.name, terms)): continue
        if city and city not in (biz.city or ""): continue
        if q:
            ql = q.lower()
            if ql not in (biz.name or "").lower() and ql not in (biz.city or "").lower(): continue
        result.append(_biz_to_dict(biz, "building" if biz.id in draft_ids else "pending"))
    return {"businesses": result[:limit]}


@router.get("/search")
def search_businesses(q: str = Query(..., min_length=1), limit: int = Query(30, le=100), db: Session = Depends(get_db)):
    ql = q.lower(); result: list[dict] = []
    for d in db.query(DemoSite).filter(DemoSite.slug.isnot(None)).all():
        if ql in (d.business_name or "").lower() or ql in (d.city or "").lower() or ql in (d.category or "").lower():
            result.append(_demo_to_dict(d))
    draft_ids = {r[0] for r in db.query(DraftSite.business_id).all()}
    for biz in db.query(Business).filter(Business.status != "deleted").all():
        if ql in (biz.name or "").lower() or ql in (biz.city or "").lower() or ql in (biz.category or "").lower():
            result.append(_biz_to_dict(biz, "building" if biz.id in draft_ids else "pending"))
    return {"businesses": result[:limit]}


@router.get("/featured")
def featured(limit: int = Query(8, le=20), db: Session = Depends(get_db)):
    demos = (db.query(DemoSite).filter(DemoSite.slug.isnot(None))
             .order_by(DemoSite.rating.desc().nullslast()).limit(limit).all())
    return {"businesses": [_demo_to_dict(d) for d in demos]}


# ──────────────────────────────────────────────────────────────────────────────
# NEARBY SEARCH — Google Places Nearby API + cross-check with our DB
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/nearby")
async def nearby_businesses(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    q: str = Query(..., min_length=1),
    radius: int = Query(5000, ge=100, le=15000),
    limit: int = Query(10, le=20),
    db: Session = Depends(get_db),
):
    """
    Returns up to 10 businesses near (lat, lng) that match query q.
    Each result includes whether it already exists in TAZO.
    If in TAZO → returns subdomain URL.
    If not → frontend can call /build-from-place.
    """
    from app.core.config import settings

    api_key = settings.google_places_api_key
    results: list[dict] = []

    if api_key:
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                resp = await client.get(
                    PLACES_NEARBY_URL,
                    params={
                        "location": f"{lat},{lng}",
                        "radius": radius,
                        "keyword": q,
                        "key": api_key,
                        "language": "iw",
                        "rankby": "prominence",
                    },
                )
                places = resp.json().get("results", [])[:limit * 2]
        except Exception as e:
            logger.warning(f"nearby places error: {e}")
            places = []

        # Deduplicate and enrich
        seen_ids: set[str] = set()
        for place in places:
            place_id = place.get("place_id", "")
            if not place_id or place_id in seen_ids:
                continue
            seen_ids.add(place_id)

            geo = place.get("geometry", {}).get("location", {})
            plat = geo.get("lat", lat)
            plng = geo.get("lng", lng)
            dist_km = round(_haversine(lat, lng, plat, plng), 2)

            # Check if in our TAZO DB
            in_db = db.query(DemoSite).filter(DemoSite.place_id == place_id).first()

            photos = place.get("photos", [])
            photo_url = ""
            if photos and api_key:
                photo_ref = photos[0].get("photo_reference", "")
                if photo_ref:
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=600&photo_reference={photo_ref}&key={api_key}"
            open_now = place.get("opening_hours", {}).get("open_now")
            place_category = _types_to_category(place.get("types", []))

            results.append({
                "place_id": place_id,
                "name": place.get("name", ""),
                "address": place.get("vicinity", ""),
                "rating": place.get("rating"),
                "reviews_count": place.get("user_ratings_total", 0),
                "lat": plat,
                "lng": plng,
                "distance_km": dist_km,
                "in_tazo": bool(in_db),
                "subdomain": in_db.slug if in_db else None,
                "url": f"https://{in_db.slug}.tazo-web.com" if in_db and in_db.slug else None,
                "status": "active" if in_db else "available",
                "photo_url": photo_url,
                "open_now": open_now,
                "category": place_category,
            })
            if len(results) >= limit:
                break

        # Sort: closest first
        results.sort(key=lambda x: x["distance_km"])

    # ── DB fallback when Google Places API key is not configured ────────
    if not results:
        from app.models.demo_site import DemoSite as _DS
        ql = q.lower()
        terms = CATEGORY_KEYWORDS.get(ql, [ql])
        db_results = []
        for d in (db.query(_DS).filter(_DS.slug.isnot(None))
                  .order_by(_DS.reviews_count.desc()).all()):
            if not (_matches(d.category, terms) or _matches(d.business_name, terms)):
                continue
            db_results.append({
                "place_id": d.place_id or f"tazo-{d.slug}",
                "name": d.business_name or "",
                "address": d.address or d.city or "",
                "rating": float(d.rating) if d.rating else None,
                "reviews_count": d.reviews_count or 0,
                "lat": lat,
                "lng": lng,
                "distance_km": 0.0,
                "in_tazo": True,
                "subdomain": d.slug,
                "url": f"https://{d.slug}.tazo-web.com" if d.slug else None,
                "status": "active",
                "photo_url": getattr(d, "photo_url", None) or "",
                "open_now": None,
                "category": d.category or ql,
            })
            if len(db_results) >= limit:
                break
        results = db_results

    return {"businesses": results, "count": len(results), "lat": lat, "lng": lng}


# ──────────────────────────────────────────────────────────────────────────────
# BUILD FROM PLACE — Create a TAZO site from a Google Places ID
# ──────────────────────────────────────────────────────────────────────────────

class BuildFromPlaceRequest(BaseModel):
    place_id: str
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    @field_validator("place_id")
    @classmethod
    def _clean_id(cls, v):
        return re.sub(r"[^A-Za-z0-9_\-]", "", v)[:150]


@router.post("/build-from-place")
async def build_from_place(payload: BuildFromPlaceRequest, db: Session = Depends(get_db)):
    """
    Given a Google Place ID, look up the business, create a Business record,
    and trigger an async site build + WhatsApp notification to the owner.
    """
    from app.core.config import settings
    import asyncio

    # Already in our DB?
    existing_demo = db.query(DemoSite).filter(DemoSite.place_id == payload.place_id).first()
    if existing_demo:
        return {
            "status": "exists",
            "subdomain": existing_demo.slug,
            "url": f"https://{existing_demo.slug}.tazo-web.com" if existing_demo.slug else None,
        }

    # Fetch full place details from Google Places
    place_data: dict = {}
    if settings.google_places_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    PLACES_DETAILS_URL,
                    params={
                        "place_id": payload.place_id,
                        "fields": DETAIL_FIELDS,
                        "key": settings.google_places_api_key,
                        "language": "iw",
                    },
                )
                place_data = resp.json().get("result", {})
        except Exception as e:
            logger.warning(f"places detail error: {e}")

    name = (place_data.get("name") or payload.name or "").strip()
    address = place_data.get("formatted_address") or place_data.get("vicinity") or payload.address or ""
    phone = place_data.get("formatted_phone_number") or payload.phone or ""
    rating = place_data.get("rating") or payload.rating
    reviews = place_data.get("user_ratings_total") or payload.reviews_count
    geo = (place_data.get("geometry") or {}).get("location", {})
    city = _extract_city(address)
    types = place_data.get("types", [])
    category = _types_to_category(types)

    if not name:
        return {"status": "error", "detail": "Could not fetch business name"}

    # Check if Business already exists (by name + city)
    existing_biz = db.query(Business).filter(
        Business.name.ilike(f"%{name}%"),
        Business.city == city,
    ).first()

    if existing_biz:
        biz = existing_biz
    else:
        biz = Business(
            name=name, city=city, category=category,
            phone=phone, address=address, status="new",
        )
        db.add(biz)
        db.commit()
        db.refresh(biz)

    # Trigger async build
    async def _run():
        try:
            import asyncio as _aio
            from app.services.draft_sites.draft_site_service import DraftSiteService
            draft = await _aio.to_thread(DraftSiteService().create_and_preview, db, biz.id)
            if p := phone:
                await _owner_wa(name, p, getattr(draft, "preview_url", None), None)
        except Exception as e:
            logger.exception(f"build-from-place async error biz={biz.id}: {e}")

    # Notify tazo-sync to create shadow business panel
    asyncio.create_task(_notify_tazo_sync(
        place_id=payload.place_id,
        name=name,
        phone=phone,
        address=address,
        city=city,
        category=category,
        rating=float(rating or 0),
        lat=geo.get("lat") if geo else None,
        lng=geo.get("lng") if geo else None,
        website=place_data.get("website", ""),
    ))
    asyncio.create_task(_run())
    return {"status": "building", "business_id": biz.id, "business_name": name}


def _extract_city(address: str) -> str:
    """Extract city from Israeli address string."""
    parts = [p.strip() for p in address.split(",")]
    for p in reversed(parts):
        if p and not p.lstrip("0123456789 "):
            continue
        if len(p) > 2 and not any(c.isdigit() for c in p):
            return p
    return parts[-1] if parts else ""


def _types_to_category(types: list[str]) -> str:
    type_map = {
        "restaurant": "food", "food": "food", "meal_delivery": "food", "meal_takeaway": "food",
        "bakery": "cafe", "cafe": "cafe", "coffee_shop": "cafe",
        "hair_care": "beauty", "beauty_salon": "beauty", "nail_salon": "beauty", "spa": "beauty",
        "gym": "health", "physiotherapist": "health", "health": "health",
        "car_repair": "vehicles", "car_dealer": "vehicles",
        "general_contractor": "repairs",
        "electrician": "electric",
        "veterinary_care": "pets", "pet_store": "pets",
        "school": "education", "university": "education",
        "event_venue": "events", "wedding_venue": "events",
    }
    for t in types:
        if t in type_map:
            return type_map[t]
    return "general"


# ──────────────────────────────────────────────────────────────────────────────
# Existing endpoints (unchanged)
# ──────────────────────────────────────────────────────────────────────────────

class TriggerBuildRequest(BaseModel):
    business_id: Optional[int] = None
    business_name: Optional[str] = None
    @field_validator("business_name")
    @classmethod
    def _clean(cls, v): return re.sub(r"<[^>]+>", "", v).strip()[:200] if v else v

@router.post("/trigger-build")
async def trigger_build(payload: TriggerBuildRequest, db: Session = Depends(get_db)):
    biz = None
    if payload.business_id:
        biz = db.query(Business).filter(Business.id == payload.business_id).first()
    if not biz and payload.business_name:
        biz = db.query(Business).filter(Business.name.ilike(f"%{payload.business_name.strip()}%")).first()
    if not biz:
        return {"status": "queued"}
    existing = db.query(DraftSite).filter(DraftSite.business_id == biz.id).first()
    if existing:
        s = getattr(existing, "status", "draft")
        return {"status": "already_active" if s in ("published_preview","published","approved") else "already_building"}
    import asyncio
    async def _run():
        try:
            from app.services.draft_sites.draft_site_service import DraftSiteService
            draft = await asyncio.to_thread(DraftSiteService().create_and_preview, db, biz.id)
            if p := getattr(biz, "phone", None):
                from app.models.demo_site import DemoSite as _DS
                from app.services.public.site_domain_service import normalize_dns_label as _ndl
                demo_obj = db.query(_DS).filter(_DS.business_name == biz.name).first()
                demo_url = None
                if demo_obj and demo_obj.slug:
                    slug = _ndl(demo_obj.slug)
                    demo_url = f"https://{slug}.tazo-web.com"
                await _owner_wa(biz.name, p, getattr(draft, "preview_url", None), demo_url)
        except Exception as e:
            logger.exception(f"trigger-build error biz={biz.id}: {e}")
    # Notify tazo-sync to create shadow business panel
    asyncio.create_task(_notify_tazo_sync(
        place_id=payload.place_id,
        name=name,
        phone=phone,
        address=address,
        city=city,
        category=category,
        rating=float(rating or 0),
        lat=geo.get("lat") if geo else None,
        lng=geo.get("lng") if geo else None,
        website=place_data.get("website", ""),
    ))
    asyncio.create_task(_run())
    return {"status": "building", "business_id": biz.id, "business_name": biz.name}


async def _owner_wa(name: str, phone: str, preview: str | None, demo_url: str | None = None):
    c = re.sub(r"\D", "", phone)
    if c.startswith("0"): c = "972" + c[1:]
    site_link = demo_url or preview or "https://tazo-web.com"
    msg = (
        f"\u05e9\u05dc\u05d5\u05dd! \U0001f44b\n\n"
        f"\u05dc\u05e7\u05d5\u05d7 \u05d7\u05d9\u05e4\u05e9 \u05d0\u05ea *{name}* \u05d1-TAZO Mall \U0001f6d2\n\n"
        f"\u05d1\u05e0\u05d9\u05e0\u05d5 \u05dc\u05db\u05dd \u05d0\u05ea\u05e8 \u05d3\u05d9\u05d2\u05d9\u05d8\u05dc\u05d9 *\u05d7\u05d9\u05e0\u05de\u05d9* \u05ea\u05d5\u05da \u05d3\u05e7\u05d5\u05ea:\n"
        f"\U0001f310 {site_link}\n\n"
        f"\u2705 *\u05dc\u05d0\u05d9\u05e9\u05d5\u05e8 \u05d5\u05e4\u05e8\u05e1\u05d5\u05dd \u05d4\u05d0\u05ea\u05e8* \u2014 \u05d4\u05e9\u05d9\u05d1\u05d5: *\u05d0\u05d9\u05e9\u05d5\u05e8*\n\n"
        f"\u270f\ufe0f *\u05dc\u05e2\u05e8\u05d9\u05db\u05ea \u05d4\u05d0\u05ea\u05e8* \u2014 \u05d1\u05e7\u05e8\u05d5 \u05d1:\nhttps://tazo-web.com\n\n"
        f"\U0001f4e6 *\u05dc\u05e0\u05d9\u05d4\u05d5\u05dc \u05d4\u05d6\u05de\u05e0\u05d5\u05ea \u05d5\u05d0\u05d9\u05de\u05d5\u05ea \u05e2\u05e1\u05e7*:\nhttps://tazo-sync.com\n\n"
        f"\u05e9\u05d0\u05dc\u05d5\u05ea? \U0001f4ac https://wa.me/972546363350"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as cl:
            await cl.post("http://sitenest-evolution:8080/message/sendText/tazo-main",
                json={"number": c, "text": msg},
                headers={"apikey": "tazo-evo-key"})
    except Exception as e:
        logger.warning(f"owner WA failed: {e}")


class NotifyMeRequest(BaseModel):
    phone: str; business_id: Optional[int] = None; business_name: Optional[str] = None
    @field_validator("phone")
    @classmethod
    def _vp(cls, v):
        c = re.sub(r"\D", "", v)
        if not (9 <= len(c) <= 15): raise ValueError("Invalid phone")
        return c

@router.post("/notify-me")
async def notify_me(payload: NotifyMeRequest):
    phone = payload.phone
    if phone.startswith("0"): phone = "972" + phone[1:]
    name = payload.business_name or "\u05d4\u05e2\u05e1\u05e7"
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            await c.post("http://sitenest-evolution:8080/message/sendText/tazo-main",
                json={"number": phone, "text": f"\u05e9\u05dc\u05d5\u05dd! \U0001f44b\n\n\u05e0\u05e8\u05e9\u05de\u05ea \u05dc\u05d4\u05ea\u05e8\u05d0\u05d4 \u05e2\u05d1\u05d5\u05e8 *{name}* \u05d1-TAZO Mall.\n\u05d1\u05e8\u05d2\u05e2 \u05e9\u05d4\u05d0\u05ea\u05e8 \u05d9\u05e2\u05dc\u05d4 \u2014 \u05e0\u05e9\u05dc\u05d7 \u05dc\u05da \u05e7\u05d9\u05e9\u05d5\u05e8.\n\n\u05e6\u05d5\u05d5\u05ea TAZO \U0001f310"},
                headers={"apikey": "tazo-evo-key"})
    except Exception as e:
        logger.warning(f"notify-me WA failed: {e}")
    return {"status": "ok"}
