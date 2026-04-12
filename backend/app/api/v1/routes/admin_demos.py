from __future__ import annotations

import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.demo_site import DemoSite
from app.services.public.site_domain_service import build_demo_public_url, normalize_dns_label

router = APIRouter(prefix='/admin/demos', tags=['admin-demos'])

# ---------------------------------------------------------------------------
# Tagline & theme helpers
# ---------------------------------------------------------------------------
_TAGLINES: dict[str, str] = {
    'מספרה': 'תספורות מקצועיות בסביבה נעימה ✂️',
    'ספרות': 'תספורות מקצועיות בסביבה נעימה ✂️',
    'מוסך': 'תיקון רכבים מהיר ואמין 🔧',
    'מכונאות': 'שירות מכונאות מקצועי לכל דגמי הרכב 🔧',
    'גנן': 'גינות יפות ומטופחות לבית ולגינה 🌿',
    'גינון': 'גינות יפות ומטופחות לבית ולגינה 🌿',
    'שרברב': 'תיקוני אינסטלציה מהיר ומקצועי 🔩',
    'אינסטלציה': 'תיקוני אינסטלציה מהיר ומקצועי 🔩',
    'חשמלאי': 'שירות חשמל מהיר ובטוח ⚡',
    'מזגן': 'התקנה ותיקון מזגנים בכל העיר 🌀',
    'שיפוצ': 'שיפוצים לבית ולמשרד 🏗️',
    'ניקיון': 'ניקיון מקצועי לכל סוגי המרחבים 🧹',
    'יופי': 'יופי וטיפוח לאישה המודרנית 💄',
    'ציפורניים': 'ציפורניים עם סגנון ואהבה 💅',
    'גריל': 'בשר טרי על הגריל — כמו בבית 🥩',
    'פיצה': 'פיצה טרייה על בצק דק ופריך 🍕',
    'קפה': 'קפה ועוגות בסביבה נעימה ☕',
    'מאפיה': 'מאפים טריים מהתנור כל בוקר 🥐',
    'מאפייה': 'מאפים טריים מהתנור כל בוקר 🥐',
    'וטרינר': 'טיפול אוהב ומקצועי לחיות המחמד 🐾',
    'פיזיותרפיה': 'חזרה לתנועה — פחות כאב, יותר חיים 🦴',
    'יוגה': 'שקט נפשי ובריאות הגוף יחד 🧘',
    'פילאטיס': 'פילאטיס לחיזוק הגוף ושיפור היציבה 🤸',
    'מכבסה': 'כביסה נקייה ומסודרת בזמן ⏱️',
    'גן ילדים': 'צמיחה, למידה ושמחה בסביבה בטוחה 🌈',
    'פרחים': 'פרחים טריים לכל אירוע ורגע מיוחד 🌸',
}


def _guess_tagline(biz: dict) -> str:
    text = f"{biz.get('category', '')} {biz.get('business_types', '')}".lower()
    for key, val in _TAGLINES.items():
        if key in text or key.lower() in text:
            return val
    return 'שירות מקצועי ואמין — ברמה הגבוהה ביותר ✨'


_CATEGORY_SLUG: dict[str, str] = {
    'מספרה': 'barber', 'ספרות': 'barber', 'מוסך': 'garage',
    'מכונאות': 'garage', 'גנן': 'garden', 'גינון': 'garden',
    'שרברב': 'plumber', 'אינסטלציה': 'plumber',
    'חשמלאי': 'electric', 'מזגן': 'ac', 'שיפוצ': 'renovate',
    'ניקיון': 'clean', 'יופי': 'beauty', 'ציפורניים': 'nails',
    'גריל': 'grill', 'פיצ': 'pizza', 'קפה': 'cafe',
    'מאפיה': 'bakery', 'מאפייה': 'bakery', 'וטרינר': 'vet',
    'פיזיותרפיה': 'physio', 'יוגה': 'yoga', 'פילאטיס': 'pilates',
    'מכבסה': 'laundry', 'גן ילדים': 'daycare', 'פרחים': 'flowers',
}


def _category_slug_prefix(biz: dict) -> str:
    text = f"{biz.get('category', '')} {biz.get('business_types', '')}".lower()
    for key, val in _CATEGORY_SLUG.items():
        if key in text:
            return val
    return 'biz'


def _extract_city(address: str) -> str:
    parts = [p.strip() for p in address.split(',') if p.strip()]
    return parts[-1] if parts else ''


def _make_slug(db: Session, prefix: str = 'biz') -> str:
    safe_prefix = normalize_dns_label(prefix)[:20] or 'biz'
    for _ in range(10):
        slug = f"{safe_prefix}-{secrets.token_hex(4)}"
        if not db.execute(select(DemoSite).where(DemoSite.slug == slug)).scalar_one_or_none():
            return slug
    raise RuntimeError('Could not generate unique slug')


def _serialize(d: DemoSite) -> dict:
    return {
        'id': d.id,
        'slug': d.slug,
        'public_url': build_demo_public_url(d.slug),
        'place_id': d.place_id,
        'business_name': d.business_name,
        'tagline': d.tagline,
        'phone': d.phone,
        'address': d.address,
        'city': d.city,
        'rating': d.rating,
        'reviews_count': d.reviews_count,
        'google_maps_url': d.google_maps_url,
        'top_review': d.top_review,
        'business_types': d.business_types,
        'category': d.category,
        'status': d.status,
        'view_count': d.view_count,
        'first_viewed_at': d.first_viewed_at.isoformat() if d.first_viewed_at else None,
        'whatsapp_sent_at': d.whatsapp_sent_at.isoformat() if d.whatsapp_sent_at else None,
        'created_at': d.created_at.isoformat() if d.created_at else None,
    }


# ---------------------------------------------------------------------------
# POST /admin/demos/create-from-enriched
# ---------------------------------------------------------------------------
class CreateFromEnrichedPayload(BaseModel):
    businesses: list[dict]


@router.post('/create-from-enriched')
def create_demos_from_enriched(
    payload: CreateFromEnrichedPayload,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Given a list of enriched business dicts (from the Enrich search),
    create DemoSite records for each one.  If a place_id already has a demo,
    return the existing record instead.
    """
    created = []
    for biz in payload.businesses:
        place_id = biz.get('place_id') or None

        # Avoid duplicates
        if place_id:
            existing = db.execute(
                select(DemoSite).where(DemoSite.place_id == place_id)
            ).scalar_one_or_none()
            if existing:
                created.append(_serialize(existing))
                continue

        types_val = biz.get('types', [])
        types_str = ', '.join(types_val) if isinstance(types_val, list) else str(types_val or '')
        address = biz.get('address', '')

        demo = DemoSite(
            slug=_make_slug(db, _category_slug_prefix(biz)),
            place_id=place_id,
            business_name=biz.get('name', 'עסק'),
            tagline=_guess_tagline(biz),
            phone=biz.get('phone'),
            address=address,
            city=biz.get('city') or _extract_city(address),
            rating=biz.get('rating'),
            reviews_count=biz.get('reviews_count'),
            google_maps_url=biz.get('google_maps_url'),
            top_review=biz.get('top_review'),
            business_types=types_str,
            category=biz.get('category'),
            status='draft',
        )
        db.add(demo)
        db.flush()
        created.append(_serialize(demo))

    db.commit()
    return {'created': len(created), 'demos': created}


# ---------------------------------------------------------------------------
# GET /admin/demos
# ---------------------------------------------------------------------------
@router.get('')
def list_demos(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    demos = db.execute(
        select(DemoSite).order_by(DemoSite.created_at.desc())
    ).scalars().all()
    return [_serialize(d) for d in demos]


# ---------------------------------------------------------------------------
# POST /admin/demos/{demo_id}/mark-sent
# ---------------------------------------------------------------------------
@router.post('/{demo_id}/mark-sent')
def mark_sent(
    demo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    demo = db.get(DemoSite, demo_id)
    if not demo:
        raise HTTPException(404, 'Demo not found')
    demo.status = 'sent'
    demo.whatsapp_sent_at = datetime.now(timezone.utc)
    db.commit()
    return _serialize(demo)


# ---------------------------------------------------------------------------
# POST /admin/demos/{demo_id}/mark-converted
# ---------------------------------------------------------------------------
@router.post('/{demo_id}/mark-converted')
def mark_converted(
    demo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    demo = db.get(DemoSite, demo_id)
    if not demo:
        raise HTTPException(404, 'Demo not found')
    demo.status = 'converted'
    db.commit()
    return _serialize(demo)


# ---------------------------------------------------------------------------
# DELETE /admin/demos/{demo_id}
# ---------------------------------------------------------------------------
@router.delete('/{demo_id}')
def delete_demo(
    demo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    demo = db.get(DemoSite, demo_id)
    if not demo:
        raise HTTPException(404, 'Demo not found')
    db.delete(demo)
    db.commit()
    return {'ok': True}
