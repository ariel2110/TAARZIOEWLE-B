#!/usr/bin/env python3
"""
enrich_all_sites.py
-------------------
Backfill existing DemoSite rows with Google Places Details data.

Examples:
    docker exec localbiz-backend python3 scripts/enrich_all_sites.py
    docker exec localbiz-backend python3 scripts/enrich_all_sites.py --limit 50
    docker exec localbiz-backend python3 scripts/enrich_all_sites.py --slug some-slug
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.business import Business
from app.models.demo_site import DemoSite
from app.services.enrichment.places_service import PlacesService


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("enrich-sites")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

KNOWN_CITIES = [
    "תל אביב", "ירושלים", "חיפה", "ראשון לציון", "פתח תקווה", "אשדוד",
    "נתניה", "באר שבע", "רמת גן", "בני ברק", "הרצליה", "כפר סבא",
    "רחובות", "חולון", "ראש העין", "מודיעין", "אשקלון", "טבריה",
]


def _extract_city(address: str, fallback: str | None) -> str | None:
    text = (address or "").strip()
    for city in KNOWN_CITIES:
        if city in text:
            return city
    return fallback


def _reviews_json(raw_reviews: list[dict] | None) -> str | None:
    cleaned = []
    for review in raw_reviews or []:
        text = str(review.get("text") or "").strip()
        if not text:
            continue
        cleaned.append({
            "author_name": review.get("author_name") or "לקוח/ה",
            "rating": review.get("rating") or 5,
            "text": text,
            "relative_time_description": review.get("relative_time_description") or "",
        })
    return json.dumps(cleaned[:5], ensure_ascii=False) if cleaned else None


def _needs_enrichment() -> object:
    return or_(
        DemoSite.opening_hours.is_(None), DemoSite.opening_hours == "",
        DemoSite.reviews_json.is_(None), DemoSite.reviews_json == "",
        DemoSite.phone.is_(None), DemoSite.phone == "",
        DemoSite.website.is_(None), DemoSite.website == "",
        DemoSite.photo_url.is_(None), DemoSite.photo_url == "",
    )


def _apply_business_updates(business: Business | None, data: dict, city: str | None) -> None:
    if business is None:
        return
    business.city = city or business.city
    business.phone = data.get("phone") or business.phone
    business.address = data.get("address") or business.address
    business.rating = float(data["rating"]) if data.get("rating") is not None else business.rating
    business.photo_url = data.get("photo_url") or business.photo_url
    business.website = data.get("website") or business.website


def _apply_site_updates(site: DemoSite, raw: dict, data: dict) -> None:
    address = data.get("address") or site.address
    city = _extract_city(address or "", site.city)
    site.business_name = data.get("name") or site.business_name
    site.phone = data.get("phone") or site.phone
    site.address = address
    site.city = city or site.city
    site.rating = float(data["rating"]) if data.get("rating") is not None else site.rating
    site.reviews_count = int(data["reviews_count"]) if data.get("reviews_count") else site.reviews_count
    site.google_maps_url = data.get("google_maps_url") or site.google_maps_url
    site.top_review = data.get("top_review") or site.top_review
    site.business_types = ", ".join(data.get("types") or [])[:500] if data.get("types") else site.business_types
    site.website = data.get("website") or site.website
    site.photo_url = data.get("photo_url") or site.photo_url
    if data.get("opening_hours"):
        site.opening_hours = json.dumps(data["opening_hours"], ensure_ascii=False)
    reviews_json = _reviews_json(raw.get("reviews") or [])
    if reviews_json:
        site.reviews_json = reviews_json
    elif not site.reviews_json:
        site.reviews_json = "[]"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich existing DemoSite rows using Google Places Details.")
    parser.add_argument("--limit", type=int, default=0, help="Optional cap on number of sites to enrich")
    parser.add_argument("--slug", type=str, default="", help="Only enrich a single slug")
    parser.add_argument("--all", action="store_true", help="Enrich all rows with place_id, not only missing fields")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be updated without committing")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    db: Session = SessionLocal()
    service = PlacesService()

    try:
        query = db.query(DemoSite).filter(DemoSite.place_id.isnot(None))
        if args.slug:
            query = query.filter(DemoSite.slug == args.slug)
        if not args.all:
            query = query.filter(_needs_enrichment())
        if args.limit:
            query = query.limit(args.limit)

        sites = query.order_by(DemoSite.id).all()
        log.info("Found %d site(s) to enrich", len(sites))

        enriched = 0
        for site in sites:
            raw = service._get_place_detail(site.place_id or "")
            if not raw:
                log.warning("Skipping %s: no details for place_id=%s", site.slug, site.place_id)
                continue

            data = service._normalize(raw)
            if args.dry_run:
                log.info("[DRY-RUN] %s | %s | phone=%s | website=%s | hours=%s | reviews=%s",
                         site.slug,
                         data.get("name") or site.business_name,
                         bool(data.get("phone")),
                         bool(data.get("website")),
                         len(data.get("opening_hours") or []),
                         len(raw.get("reviews") or []))
                enriched += 1
                continue

            try:
                _apply_site_updates(site, raw, data)
                business = db.query(Business).filter(Business.id == site.business_id).first() if site.business_id else None
                _apply_business_updates(business, data, site.city)
                db.commit()
                enriched += 1
                log.debug("enriched %s (%s)", site.slug, site.business_name)
            except Exception:
                db.rollback()
                raise

        mode = "would enrich" if args.dry_run else "enriched"
        log.info("Done: %s %d site(s)", mode, enriched)
    finally:
        db.close()


if __name__ == "__main__":
    main()