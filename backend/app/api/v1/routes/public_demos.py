from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import Depends

from app.db.session import get_db
from app.models.demo_site import DemoSite

router = APIRouter(prefix='/public/demo', tags=['public-demo'])


@router.get('/{slug}')
def get_public_demo(slug: str, db: Session = Depends(get_db)):
    """
    Public endpoint — no authentication required.
    Returns the data needed to render a demo website.
    """
    demo = db.execute(
        select(DemoSite).where(DemoSite.slug == slug)
    ).scalar_one_or_none()
    if not demo:
        raise HTTPException(404, 'Demo not found')

    return {
        'slug': demo.slug,
        'business_name': demo.business_name,
        'tagline': demo.tagline,
        'phone': demo.phone,
        'address': demo.address,
        'city': demo.city,
        'rating': demo.rating,
        'reviews_count': demo.reviews_count,
        'google_maps_url': demo.google_maps_url,
        'top_review': demo.top_review,
        'business_types': demo.business_types,
        'category': demo.category,
    }


@router.post('/{slug}/view')
def track_view(slug: str, db: Session = Depends(get_db)):
    """
    Called by the demo page on first load to increment view counter.
    Public — no auth.
    """
    demo = db.execute(
        select(DemoSite).where(DemoSite.slug == slug)
    ).scalar_one_or_none()
    if not demo:
        raise HTTPException(404, 'Demo not found')

    demo.view_count = (demo.view_count or 0) + 1
    if not demo.first_viewed_at:
        demo.first_viewed_at = datetime.now(timezone.utc)
    if demo.status in ('draft', 'sent'):
        demo.status = 'viewed'

    db.commit()
    return {'ok': True, 'view_count': demo.view_count}
