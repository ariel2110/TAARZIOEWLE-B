
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

router = APIRouter(prefix='/admin/leads', tags=['admin-leads'])
service = LeadImportService()

# ── Hot-lead scoring ──────────────────────────────────────────────────────────
# Categories that historically convert well for website outreach (higher weight)
_PRIORITY_CATEGORIES = {
    'beauty', 'hair', 'salon', 'spa', 'nails', 'barber',
    'restaurant', 'cafe', 'bakery',
    'car', 'auto', 'mechanic', 'garage',
    'dentist', 'doctor', 'clinic', 'medical',
    'lawyer', 'attorney', 'legal',
    'gym', 'fitness', 'yoga',
    'plumber', 'electrician', 'contractor',
}

# Thresholds that define a "hot" lead — a business that DESERVES a website
# but doesn't have one (or has a broken one).
_HOT_REVIEWS_MIN = 20      # Proven track record
_HOT_RATING_MIN = 4.3      # Customers love them
_WARM_REVIEWS_MIN = 10     # Decent presence but not yet hot
_WARM_RATING_MIN = 4.0


def _has_website(lead: LeadRecord) -> bool:
    url = (lead.website_url or '').strip()
    return bool(url and url.lower() not in ('none', 'n/a', '-'))


def classify_lead_hotness(lead: LeadRecord) -> tuple[str, int]:
    """
    Return (tier, computed_score) for a lead.

    Tiers:
      'hot'   — >20 reviews, rating ≥4.3, no working website  → score 90+
      'warm'  — ≥10 reviews, rating ≥4.0, no working website  → score 70-89
      'cold'  — everything else                                → score <70

    The returned score replaces the generic import score so the leads page
    shows meaningful priority ordering.
    """
    reviews = lead.reviews_count or 0
    rating = lead.rating or 0.0
    no_site = not _has_website(lead)
    category_lower = (lead.category or '').lower()
    is_priority_category = any(kw in category_lower for kw in _PRIORITY_CATEGORIES)

    score = 0

    # ── Review volume signal (0-30 pts) ──────────────────────
    if reviews >= 50:
        score += 30
    elif reviews >= 20:
        score += 20
    elif reviews >= 10:
        score += 10
    elif reviews >= 5:
        score += 5

    # ── Rating signal (0-30 pts) ──────────────────────────────
    if rating >= 4.7:
        score += 30
    elif rating >= 4.3:
        score += 20
    elif rating >= 4.0:
        score += 10
    elif rating >= 3.5:
        score += 5

    # ── Missing website — core opportunity signal (0-30 pts) ──
    if no_site:
        score += 30

    # ── Category bonus (0-10 pts) ─────────────────────────────
    if is_priority_category:
        score += 10

    # Determine tier
    is_hot = (reviews >= _HOT_REVIEWS_MIN and rating >= _HOT_RATING_MIN and no_site)
    is_warm = (reviews >= _WARM_REVIEWS_MIN and rating >= _WARM_RATING_MIN and no_site)

    if is_hot:
        tier = 'hot'
    elif is_warm:
        tier = 'warm'
    else:
        tier = 'cold'

    return tier, min(score, 100)


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
