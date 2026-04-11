
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadRead, LeadAssignCampaign
from app.schemas.business import BusinessRead
from app.services.leads.lead_import_service import LeadImportService
from app.models.user import User
from app.models.lead_record import LeadRecord
from app.models.activity_log import ActivityLog
import math

router = APIRouter(prefix='/admin/leads', tags=['admin-leads'])
service = LeadImportService()

# ── Hot-lead scoring ──────────────────────────────────────────────────────────
# Categories historically best for website conversion (category bonus)
_PRIORITY_CATEGORIES = {
    'beauty', 'hair', 'salon', 'spa', 'nails', 'barber',
    'restaurant', 'cafe', 'bakery',
    'car', 'auto', 'mechanic', 'garage',
    'dentist', 'doctor', 'clinic', 'medical',
    'lawyer', 'attorney', 'legal',
    'gym', 'fitness', 'yoga',
    'plumber', 'electrician', 'contractor',
}

# Tier thresholds — a "hot" lead has proven demand (reviews) + quality (rating)
# but NO website to handle that demand.
_HOT_REVIEWS_MIN = 20
_HOT_RATING_MIN = 4.3
_WARM_REVIEWS_MIN = 10
_WARM_RATING_MIN = 4.0


def _has_website(lead: LeadRecord) -> bool:
    url = (lead.website_url or '').strip()
    return bool(url and url.lower() not in ('none', 'n/a', '-'))


def classify_lead_hotness(lead: LeadRecord) -> tuple[str, int]:
    """
    Return (tier, computed_score) for a lead.

    Score uses a WEIGHTED RATIO formula so that volume × quality compounds:
      base_signal = reviews * log2(reviews + 1) * rating_multiplier
    This ensures 200 reviews @ 4.8 >> 5 reviews @ 5.0, which is the correct
    business reality — proven social proof beats a perfect-but-sparse record.

    Tiers (qualification gates — all three conditions must pass):
      'hot'   — reviews > 20,  rating ≥ 4.3, no website
      'warm'  — reviews ≥ 10,  rating ≥ 4.0, no website
      'cold'  — everything else

    Score is capped at 99 for cold/warm, reserved 100 for 'boiling_hot'
    (set by webhook when the business owner actively replies).
    """
    reviews = lead.reviews_count or 0
    rating = lead.rating or 0.0
    no_site = not _has_website(lead)
    category_lower = (lead.category or '').lower()
    is_priority_category = any(kw in category_lower for kw in _PRIORITY_CATEGORIES)

    # ── Weighted ratio: volume × log(volume) × quality multiplier ────────────
    # rating_multiplier: maps 0–5 → 0–2.0, super-linear above 4.3
    if rating >= 4.7:
        rating_mult = 2.0
    elif rating >= 4.3:
        rating_mult = 1.6
    elif rating >= 4.0:
        rating_mult = 1.2
    elif rating >= 3.5:
        rating_mult = 0.8
    elif rating > 0:
        rating_mult = 0.4
    else:
        rating_mult = 0.5   # unknown rating — neutral

    # log2 compress review volume so 200 reviews isn't 40× better than 5
    log_volume = math.log2(reviews + 1)          # reviews=0→0, 10→3.46, 50→5.67, 200→7.65

    # raw_signal = volume × quality, max ≈ 200*7.65*2.0 = 3060
    raw_signal = reviews * log_volume * rating_mult

    # Normalize to 0–79 (raw_signal / 3100 * 79), floor at 0
    base_score = min(int(raw_signal / 3100 * 79), 79)

    # ── Opportunity bonus: no website = opportunity exists (+15 pts) ──────────
    if no_site:
        base_score += 15

    # ── Category bonus (+5 pts) ───────────────────────────────────────────────
    if is_priority_category:
        base_score += 5

    score = min(base_score, 99)   # cap at 99; 100 is reserved for boiling_hot

    # Tier gates
    is_hot = (reviews >= _HOT_REVIEWS_MIN and rating >= _HOT_RATING_MIN and no_site)
    is_warm = (reviews >= _WARM_REVIEWS_MIN and rating >= _WARM_RATING_MIN and no_site)

    if is_hot:
        tier = 'hot'
    elif is_warm:
        tier = 'warm'
    else:
        tier = 'cold'

    return tier, score


@router.get('', response_model=list[LeadRead])
def list_leads(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_leads(db, skip=skip, limit=limit)


@router.post('', response_model=LeadRead)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_lead(db, payload)


@router.post('/import-csv')
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    content = file.file.read().decode('utf-8')
    return service.import_csv_text(db, content)


@router.post('/auto-qualify')
def auto_qualify_leads(
    min_tier: str = Query(default='warm', description='hot | warm (include hot+warm)'),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Auto-qualify leads using the hot-lead scoring formula.

    A lead is qualified if it meets ALL of:
      - tier == 'hot':  reviews_count > 20  AND  rating >= 4.3  AND  no website
      - tier == 'warm': reviews_count >= 10 AND  rating >= 4.0  AND  no website
        (passing min_tier='warm' qualifies both hot and warm leads)

    Also recalculates and saves the numeric score for every unqualified lead
    so the leads list reflects real priority ordering.
    """
    accepted_tiers = {'hot'} if min_tier == 'hot' else {'hot', 'warm'}

    candidates = (
        db.query(LeadRecord)
        .filter(LeadRecord.status == 'imported')
        .all()
    )

    qualified = []
    rescored = 0
    for lead in candidates:
        tier, computed_score = classify_lead_hotness(lead)

        # Always update score so the list has accurate ordering
        if lead.score != computed_score:
            lead.score = computed_score
            rescored += 1

        if tier in accepted_tiers:
            lead.status = 'qualified'
            db.add(ActivityLog(
                actor_type='system',
                entity_type='lead_record',
                entity_id=lead.id,
                action_type='lead_auto_qualified',
                summary=(
                    f'Auto-qualified [{tier}]: {lead.imported_name} '
                    f'(rating={lead.rating}, reviews={lead.reviews_count}, '
                    f'score={computed_score}, no_website={not _has_website(lead)})'
                ),
            ))
            qualified.append({
                'id': lead.id,
                'name': lead.imported_name,
                'tier': tier,
                'score': computed_score,
                'rating': lead.rating,
                'reviews_count': lead.reviews_count,
            })

    if candidates:
        db.commit()

    if qualified:
        try:
            from app.services.common.notification_service import NotificationService
            hot_count = sum(1 for q in qualified if q['tier'] == 'hot')
            warm_count = sum(1 for q in qualified if q['tier'] == 'warm')
            NotificationService().notify(
                db,
                event='lead_auto_qualified',
                entity_type='lead_record',
                summary=(
                    f'Auto-qualified {len(qualified)} leads: '
                    f'{hot_count} 🔥 hot, {warm_count} 🌤 warm '
                    f'(all have {_HOT_REVIEWS_MIN if min_tier == "hot" else _WARM_REVIEWS_MIN}+ reviews, high rating, no website)'
                ),
                extra={'count': str(len(qualified)), 'hot': str(hot_count), 'warm': str(warm_count)},
            )
        except Exception:  # noqa: BLE001
            pass

    return {
        'qualified': len(qualified),
        'rescored': rescored,
        'leads': qualified,
    }


@router.post('/{lead_id}/qualify', response_model=LeadRead)
def qualify_lead(lead_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.qualify(db, lead_id)
    if not item:
        raise HTTPException(status_code=404, detail='Lead not found')
    return item


@router.post('/{lead_id}/assign', response_model=LeadRead)
def assign_campaign(lead_id: int, payload: LeadAssignCampaign, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.assign_campaign(db, lead_id, payload.campaign_id, payload.targeting_profile_id)
    if not item:
        raise HTTPException(status_code=404, detail='Lead not found')
    return item


@router.post('/{lead_id}/convert-to-business', response_model=BusinessRead)
def convert_to_business(lead_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.convert_to_business(db, lead_id)
    if not item:
        raise HTTPException(status_code=404, detail='Lead not found')
    return item
