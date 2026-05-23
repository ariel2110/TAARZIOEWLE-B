"""
public_inbound.py — Magic Portal endpoints (no auth required).

Endpoints:
  GET  /public/places-autocomplete          — proxy Google Places Autocomplete
  POST /public/build-instant                — create lead+biz, dispatch Celery task
  GET  /public/task-status/{task_id}        — poll Celery task progress
  POST /public/capture-phone                — store inbound contact phone
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.common.rate_limit_service import RateLimitService

logger = logging.getLogger(__name__)
_rate_svc = RateLimitService()

router = APIRouter(prefix='/public', tags=['public-inbound'])

# ── Schemas ───────────────────────────────────────────────────────────────────

class BuildInstantRequest(BaseModel):
    place_id: str
    business_name: str | None = None
    city: str | None = None
    category: str | None = None


class BuildInstantResponse(BaseModel):
    task_id: str
    business_id: int
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str            # PENDING | PROGRESS | SUCCESS | FAILURE
    step: str | None = None
    label: str | None = None
    percent: int | None = None
    preview_url: str | None = None
    public_url: str | None = None
    error: str | None = None


class CapturePhoneRequest(BaseModel):
    business_id: int
    phone: str


# ── Helpers ───────────────────────────────────────────────────────────────────

_PLACES_AC_URL = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
_PLACES_DETAIL_URL = 'https://maps.googleapis.com/maps/api/place/details/json'
_PLACES_PHOTO_URL = 'https://maps.googleapis.com/maps/api/place/photo'
_DETAIL_FIELDS = (
    'name,formatted_address,formatted_phone_number,'
    'website,rating,user_ratings_total,opening_hours,'
    'url,vicinity,types,reviews,place_id,photos'
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get('/places-autocomplete')
def places_autocomplete(
    input: str = Query(..., min_length=2),
    session_token: str | None = Query(default=None),
):
    """Proxy Google Places Autocomplete — keeps API key server-side."""
    api_key = settings.google_places_api_key
    if not api_key:
        return {'predictions': []}
    try:
        params: dict[str, Any] = {
            'input': input,
            'key': api_key,
            'language': 'he',
            'components': 'country:il',
            'types': 'establishment',
        }
        if session_token:
            params['sessiontoken'] = session_token
        resp = httpx.get(_PLACES_AC_URL, params=params, timeout=6)
        data = resp.json()
        # Return only the fields the frontend needs
        predictions = [
            {
                'place_id': p.get('place_id'),
                'description': p.get('description'),
                'structured_formatting': p.get('structured_formatting', {}),
            }
            for p in data.get('predictions', [])
        ]
        return {'predictions': predictions}
    except Exception as exc:
        logger.warning('[places-autocomplete] error: %s', exc)
        return {'predictions': []}


@router.get('/place-detail')
def place_detail(place_id: str = Query(...), session_token: str | None = Query(default=None)):
    """Fetch details for a selected place (name, address, rating, phone)."""
    api_key = settings.google_places_api_key
    if not api_key:
        raise HTTPException(status_code=503, detail='Places API not configured')
    try:
        params: dict[str, Any] = {
            'place_id': place_id,
            'fields': _DETAIL_FIELDS,
            'key': api_key,
            'language': 'he',
        }
        if session_token:
            params['sessiontoken'] = session_token
        resp = httpx.get(_PLACES_DETAIL_URL, params=params, timeout=8)
        raw = resp.json().get('result', {})
        reviews = raw.get('reviews') or []
        photo_ref = (raw.get('photos') or [{}])[0].get('photo_reference', '') if raw.get('photos') else ''
        photo_url = (
            f'{_PLACES_PHOTO_URL}?maxwidth=400&photo_reference={photo_ref}&key={api_key}'
            if photo_ref else ''
        )
        return {
            'name': raw.get('name', ''),
            'address': raw.get('formatted_address') or raw.get('vicinity', ''),
            'phone': raw.get('formatted_phone_number') or raw.get('international_phone_number', ''),
            'website': raw.get('website', ''),
            'rating': raw.get('rating'),
            'reviews_count': raw.get('user_ratings_total'),
            'types': raw.get('types', []),
            'opening_hours': (raw.get('opening_hours') or {}).get('weekday_text', []),
            'top_review': reviews[0].get('text', '') if reviews else '',
            'google_maps_url': raw.get('url', ''),
            'photo_url': photo_url,
        }
    except Exception as exc:
        logger.warning('[place-detail] error: %s', exc)
        raise HTTPException(status_code=502, detail='Failed to fetch place details')


@router.post('/build-instant', response_model=BuildInstantResponse)
def build_instant(payload: BuildInstantRequest, request: Request, db: Session = Depends(get_db)):
    """
    Create a LeadRecord + Business from a Place selection and dispatch the
    inbound_build_task Celery task.  Rate-limit: one active task per place_id.
    """
    # Rate limit: max 5 build requests per IP per hour
    client_ip = request.headers.get('x-real-ip') or (request.client.host if request.client else 'unknown')
    allowed, count, limit = _rate_svc.check_and_record(
        db,
        scope='public_build_instant',
        key=client_ip,
        action='build',
        window_minutes=60,
        max_per_window=5,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail='יותר מדי בקשות — נסה שוב מאוחר יותר')
    from app.models.lead_record import LeadRecord
    from app.models.business import Business
    from app.models.enriched_biz_cache import EnrichedBizCache
    from app.tasks import inbound_build_task

    # ── Enrich from Google Places ─────────────────────────────────────────────
    api_key = settings.google_places_api_key
    place_data: dict = {}
    if api_key:
        try:
            resp = httpx.get(
                _PLACES_DETAIL_URL,
                params={
                    'place_id': payload.place_id,
                    'fields': _DETAIL_FIELDS,
                    'key': api_key,
                    'language': 'he',
                },
                timeout=10,
            )
            raw = resp.json().get('result', {})
            reviews = raw.get('reviews') or []
            place_data = {
                'name': raw.get('name', payload.business_name or ''),
                'address': raw.get('formatted_address') or raw.get('vicinity', ''),
                'phone': raw.get('formatted_phone_number') or raw.get('international_phone_number', ''),
                'website': raw.get('website', ''),
                'rating': raw.get('rating'),
                'reviews_count': raw.get('user_ratings_total'),
                'types': raw.get('types', []),
                'opening_hours': (raw.get('opening_hours') or {}).get('weekday_text', []),
                'top_review': reviews[0].get('text', '') if reviews else '',
                'google_maps_url': raw.get('url', ''),
            }
        except Exception as exc:
            logger.warning('[build-instant] Places enrichment failed: %s', exc)

    biz_name = place_data.get('name') or payload.business_name or 'עסק לא ידוע'
    city_guess = ''
    addr = place_data.get('address', '')
    # Simple city extraction from formatted_address (last part before country)
    parts = [p.strip() for p in addr.split(',')]
    if len(parts) >= 2:
        city_guess = parts[-2]

    # ── Upsert EnrichedBizCache ───────────────────────────────────────────────
    cache_row = db.query(EnrichedBizCache).filter(
        EnrichedBizCache.place_id == payload.place_id
    ).first()
    if not cache_row:
        cache_row = EnrichedBizCache(
            place_id=payload.place_id,
            name=biz_name,
            city=city_guess or payload.city,
            phone=place_data.get('phone'),
            address=addr,
            website=place_data.get('website'),
            rating=place_data.get('rating'),
            reviews_count=place_data.get('reviews_count'),
            business_types=','.join(place_data.get('types', [])),
            raw_json=json.dumps({
                'google_maps_url': place_data.get('google_maps_url', ''),
                'top_review': place_data.get('top_review', ''),
                'opening_hours': place_data.get('opening_hours', []),
            }, ensure_ascii=False),
        )
        db.add(cache_row)
        db.flush()

    # ── Create or reuse LeadRecord ────────────────────────────────────────────
    lead = db.query(LeadRecord).filter(
        LeadRecord.imported_name == biz_name,
        LeadRecord.notes.contains('INBOUND'),
    ).first()
    if not lead:
        lead = LeadRecord(
            imported_name=biz_name,
            city=city_guess or payload.city,
            category=payload.category or (place_data.get('types', [''])[0] if place_data.get('types') else ''),
            phone=place_data.get('phone'),
            address=addr,
            website_url=place_data.get('website'),
            rating=place_data.get('rating'),
            reviews_count=place_data.get('reviews_count'),
            status='inbound',
            notes='INBOUND',
        )
        db.add(lead)
        db.flush()

    # ── Create or reuse Business ──────────────────────────────────────────────
    business = db.query(Business).filter(
        Business.lead_id == lead.id
    ).first()
    if not business:
        business = Business(
            name=biz_name,
            city=city_guess or payload.city,
            category=payload.category or (place_data.get('types', [''])[0] if place_data.get('types') else ''),
            phone=place_data.get('phone'),
            address=addr,
            lead_id=lead.id,
            notes='INBOUND',
        )
        db.add(business)
        db.flush()

    db.commit()

    # ── Dispatch Celery task ──────────────────────────────────────────────────
    task = inbound_build_task.delay(business.id)
    logger.info('[build-instant] dispatched task %s for business_id=%d', task.id, business.id)

    return BuildInstantResponse(
        task_id=task.id,
        business_id=business.id,
        message=f'בונים אתר דמו עבור {biz_name}...',
    )


@router.get('/task-status/{task_id}', response_model=TaskStatusResponse)
def task_status(task_id: str):
    """Poll Celery task progress — no auth required."""
    result = celery_app.AsyncResult(task_id)
    state = result.state
    step: str | None = None
    label: str | None = None
    percent: int | None = None
    preview_url: str | None = None
    public_url: str | None = None
    error: str | None = None

    if state == 'PROGRESS':
        meta = result.info or {}
        step = meta.get('step')
        label = meta.get('label')
        percent = meta.get('percent')
    elif state == 'SUCCESS':
        res = result.result or {}
        step = 'done'
        percent = 100
        label = '🎉 האתר מוכן!'
        preview_url = res.get('preview_url')
        public_url = res.get('public_url')
        if res.get('status') == 'error':
            state = 'FAILURE'
            error = res.get('message')
    elif state == 'FAILURE':
        exc = result.result
        error = str(exc) if exc else 'שגיאה לא ידועה'

    return TaskStatusResponse(
        task_id=task_id,
        state=state,
        step=step,
        label=label,
        percent=percent,
        preview_url=preview_url,
        public_url=public_url,
        error=error,
    )


@router.post('/capture-phone')
def capture_phone(payload: CapturePhoneRequest, db: Session = Depends(get_db)):
    """Store the inbound contact's WhatsApp phone number on the Lead."""
    from app.models.business import Business
    from app.models.lead_record import LeadRecord

    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail='Business not found')

    # Update lead with contact phone
    if business.lead_id:
        lead = db.query(LeadRecord).filter(LeadRecord.id == business.lead_id).first()
        if lead:
            existing_notes = lead.notes or ''
            lead.notes = existing_notes + f'\nCONTACT_PHONE:{payload.phone}'
            db.commit()

    # Optionally notify CEO via Grok notification (fire-and-forget)
    try:
        logger.info('[capture-phone] Inbound lead %s submitted phone for business %s', payload.phone, business.name)
    except Exception:
        pass

    return {'status': 'ok', 'message': 'טלפון נשמר בהצלחה'}
