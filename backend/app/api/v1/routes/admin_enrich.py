from __future__ import annotations

import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.enriched_biz_cache import EnrichedBizCache
from app.services.enrichment.orchestrator import EnrichmentOrchestrator
from app.services.enrichment.places_service import PlacesService, SMALL_BIZ_CATEGORIES
from app.services.leads.lead_import_service import LeadImportService
from app.schemas.lead import LeadCreate
from app.core.config import settings

router = APIRouter(prefix='/admin/enrich', tags=['admin-enrich'])
orchestrator = EnrichmentOrchestrator()
places_svc = PlacesService()
lead_svc = LeadImportService()


# ------------------------------------------------------------------
# GET /admin/enrich/categories
# ------------------------------------------------------------------
@router.get('/categories')
def get_categories(_: User = Depends(get_current_admin)):
    """Return preset small-business categories for the search UI."""
    return SMALL_BIZ_CATEGORIES


# ------------------------------------------------------------------
# GET /admin/enrich/search
# ------------------------------------------------------------------
@router.get('/search')
def search_businesses(
    city: str = Query(default='תל אביב'),
    category: str = Query(default=''),
    limit: int = Query(default=30, ge=1, le=100),
    no_website_only: bool = Query(default=True, description='Only return businesses without a website'),
    min_reviews: int = Query(default=20, ge=0, description='Minimum Google reviews count'),
    min_rating: float = Query(default=4.0, ge=0.0, le=5.0, description='Minimum rating'),
    social: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Search for small local businesses.
    Defaults to: no website, 20+ reviews, 4.0+ rating — the best leads.
    Results are cached in DB to avoid re-fetching known businesses.
    """
    # Fetch from Places API (with smart filtering)
    raw = places_svc.search_businesses(
        city=city,
        category=category,
        limit=limit,
        no_website_only=no_website_only,
        min_reviews=min_reviews,
        min_rating=min_rating,
    )

    # Load all known place_ids for this city from cache (one query)
    existing_rows = db.execute(
        select(EnrichedBizCache.place_id, EnrichedBizCache.imported_as_lead)
        .where(EnrichedBizCache.city == city)
    ).all()
    cached_map: dict[str, bool] = {row.place_id: row.imported_as_lead for row in existing_rows}

    results = []
    new_count = 0
    known_count = 0

    for biz in raw:
        pid = biz.get("place_id", "")
        is_known = pid in cached_map
        is_imported = cached_map.get(pid, False)

        # Enrich with social if requested
        if social:
            from app.services.enrichment.social_service import SocialEnrichmentService
            social_svc = SocialEnrichmentService()
            soc = social_svc.find_social(biz.get("name", ""), biz.get("website", ""), city)
            biz.update({
                "facebook_url": soc.get("facebook_url", ""),
                "instagram_url": soc.get("instagram_url", ""),
                "social_confidence": soc.get("confidence", "low"),
                "social_sources": soc.get("sources", []),
            })
        else:
            biz.setdefault("facebook_url", "")
            biz.setdefault("instagram_url", "")
            biz.setdefault("social_confidence", "unknown")
            biz.setdefault("social_sources", [])

        biz["completeness_score"] = _completeness(biz)
        biz["lead_opportunity_score"] = _lead_opportunity(biz)
        biz["cache_status"] = "imported" if is_imported else ("known" if is_known else "new")

        # Save to cache if new
        if pid and not is_known:
            try:
                db.add(EnrichedBizCache(
                    place_id=pid,
                    name=biz.get("name", ""),
                    city=city,
                    phone=biz.get("phone"),
                    address=biz.get("address"),
                    website=biz.get("website") or None,
                    rating=biz.get("rating"),
                    reviews_count=biz.get("reviews_count"),
                    business_types=",".join(biz.get("types", [])),
                    search_query=f"{category} {city}".strip(),
                    completeness_score=biz["completeness_score"],
                    imported_as_lead=False,
                    raw_json=json.dumps(biz, ensure_ascii=False)[:4000],
                ))
                new_count += 1
            except Exception:
                db.rollback()
        else:
            known_count += 1

    try:
        db.commit()
    except Exception:
        db.rollback()

    return {
        'city': city,
        'category': category,
        'total': len(results := results or raw),  # reuse enriched list
        'new_this_search': new_count,
        'already_known': known_count,
        'filters': {
            'no_website_only': no_website_only,
            'min_reviews': min_reviews,
            'min_rating': min_rating,
        },
        'has_real_api': bool(settings.google_places_api_key),
        'results': raw,  # raw already has cache_status attached
    }


# ------------------------------------------------------------------
# POST /admin/enrich/import-to-leads
# ------------------------------------------------------------------
@router.post('/import-to-leads')
def import_to_leads(
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    businesses = payload.get('businesses', [])
    city = payload.get('city', '')
    if not businesses:
        raise HTTPException(status_code=400, detail='No businesses provided')

    imported = 0
    skipped = 0
    errors: list[str] = []

    for biz in businesses:
        pid = biz.get('place_id', '')
        try:
            lead = LeadCreate(
                imported_name=biz.get('name', 'Unknown'),
                city=(biz.get('address', city) or city).split(',')[0],
                category=', '.join(biz.get('types', [])[:2]),
                phone=biz.get('phone', ''),
                website_url=biz.get('website', ''),
                score=biz.get('completeness_score', 20),
                status='imported',
            )
            lead_svc.create_lead(db, lead)
            imported += 1

            # Mark cache entry as imported
            if pid:
                row = db.execute(
                    select(EnrichedBizCache).where(EnrichedBizCache.place_id == pid)
                ).scalar_one_or_none()
                if row:
                    row.imported_as_lead = True
        except Exception as e:
            skipped += 1
            errors.append(str(e)[:80])

    try:
        db.commit()
    except Exception:
        db.rollback()

    return {'imported': imported, 'skipped': skipped, 'errors': errors[:10]}


# ------------------------------------------------------------------
# GET /admin/enrich/cached
# ------------------------------------------------------------------
@router.get('/cached')
def get_cached_businesses(
    city: str = Query(default=''),
    limit: int = Query(default=50, ge=1, le=200),
    imported_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Return businesses already in the local cache (previously searched)."""
    stmt = select(EnrichedBizCache).order_by(
        EnrichedBizCache.reviews_count.desc().nulls_last()
    ).limit(limit)
    if city:
        stmt = stmt.where(EnrichedBizCache.city == city)
    if imported_only:
        stmt = stmt.where(EnrichedBizCache.imported_as_lead == True)
    rows = db.execute(stmt).scalars().all()
    return {
        'total': len(rows),
        'results': [
            {
                'id': r.id,
                'place_id': r.place_id,
                'name': r.name,
                'city': r.city,
                'phone': r.phone,
                'address': r.address,
                'website': r.website,
                'rating': r.rating,
                'reviews_count': r.reviews_count,
                'business_types': r.business_types,
                'completeness_score': r.completeness_score,
                'imported_as_lead': r.imported_as_lead,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


# ------------------------------------------------------------------
# GET /admin/enrich/enrich-single
# ------------------------------------------------------------------
@router.get('/enrich-single')
def enrich_single(
    place_id: str = Query(...),
    social: bool = Query(default=True),
    _: User = Depends(get_current_admin),
):
    result = orchestrator.enrich_single(place_id=place_id, include_social=social)
    if not result:
        raise HTTPException(status_code=404, detail='Place not found or no API key configured')
    return result


# ------------------------------------------------------------------
# GET /admin/enrich/status
# ------------------------------------------------------------------
@router.get('/status')
def enrich_status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    cached_total = db.execute(select(EnrichedBizCache)).scalars().all()
    imported_total = [r for r in cached_total if r.imported_as_lead]
    return {
        'google_places': bool(settings.google_places_api_key),
        'facebook_graph': bool(getattr(settings, 'facebook_access_token', None)),
        'openai_llm': bool(settings.openai_api_key),
        'mode': 'live' if settings.google_places_api_key else 'demo',
        'cache_total': len(cached_total),
        'cache_imported': len(imported_total),
    }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _completeness(biz: dict) -> int:
    score = 0
    if biz.get("name"):      score += 20
    if biz.get("phone"):     score += 25
    if biz.get("address"):   score += 15
    if biz.get("rating"):    score += 10
    if biz.get("reviews_count", 0) and biz["reviews_count"] > 10: score += 10
    if biz.get("opening_hours"): score += 10
    if biz.get("facebook_url") or biz.get("instagram_url"): score += 10
    return min(score, 100)


def _lead_opportunity(biz: dict) -> int:
    """
    How urgently does this business NEED a website?
    Higher = better lead for us.
    Max 100.
    """
    score = 0
    # No website is the core signal — worth 45 pts
    if not biz.get("website"):
        score += 45
    # High reviews = the business has demand but no online presence
    reviews = biz.get("reviews_count") or 0
    if reviews >= 200:   score += 25
    elif reviews >= 100: score += 18
    elif reviews >= 50:  score += 12
    elif reviews >= 20:  score += 6
    # High rating = happy customers, easier sell
    rating = biz.get("rating") or 0.0
    if rating >= 4.7:   score += 20
    elif rating >= 4.5: score += 15
    elif rating >= 4.0: score += 8
    # Has phone = reachable
    if biz.get("phone"): score += 10
    return min(score, 100)
