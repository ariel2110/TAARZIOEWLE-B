#!/usr/bin/env python3
"""
mass_seed_all.py
----------------
Seed demo_sites at scale using the current PlacesService and current ORM models.

Default target: 21 categories x 18 cities x 6 results per combo ~= 2268 attempts.

Examples:
    docker exec localbiz-backend python3 scripts/mass_seed_all.py
    docker exec localbiz-backend python3 scripts/mass_seed_all.py --per-combo 8 --min-reviews 20
    docker exec localbiz-backend python3 scripts/mass_seed_all.py --dry-run --limit 10
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.business import Business
from app.models.demo_site import DemoSite
from app.services.enrichment.places_service import PlacesService


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mass-seed")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

TARGET_CITIES = [
    "תל אביב", "ירושלים", "חיפה", "ראשון לציון", "פתח תקווה", "אשדוד",
    "נתניה", "באר שבע", "רמת גן", "בני ברק", "הרצליה", "כפר סבא",
    "רחובות", "חולון", "ראש העין", "מודיעין", "אשקלון", "טבריה",
]


def _slugify(text: str, place_id: str) -> str:
    base = unicodedata.normalize("NFKD", text or "biz").encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:48]
    return base or f"biz-{(place_id or 'site')[-8:].lower()}"


def _unique_slug(name: str, city: str, place_id: str, db: Session | None) -> str:
    base = _slugify(f"{name}-{city}", place_id)
    if db is None:
        return base
    slug = base
    counter = 1
    while db.query(DemoSite.id).filter(DemoSite.slug == slug).first():
        counter += 1
        slug = f"{base[:42]}-{counter}"
    return slug


def _extract_city(address: str, fallback: str) -> str:
    text = (address or "").strip()
    for city in TARGET_CITIES:
        if city in text:
            return city
    return fallback


def _category_id(label: str, types: list[str]) -> str:
    text = f"{label} {' '.join(types or [])}".lower()
    if re.search(r"pizza|restaurant|food|cafe|bakery|bar|meal|פיצה|מסעד|קפה|מאפ|שיפוד", text):
        return "food"
    if re.search(r"beauty|salon|hair|spa|nail|barber|ספר|מספרה|יופי|ציפורניים|ספא", text):
        return "beauty"
    if re.search(r"dent|physio|gym|health|yoga|pilates|veter|fitness|רופא|פיזיו|יוגה|פילאטיס|כושר|וטרינר|אופטיק", text):
        return "health"
    if re.search(r"car|repair|garage|tire|vehicle|wash|מוסך|צמיג|רכב|מכונ", text):
        return "vehicles"
    if re.search(r"plumber|electric|hvac|locksmith|clean|contractor|garden|repair|שרברב|חשמלאי|מזגן|שיפוץ|ניקיון|גנן", text):
        return "repairs"
    if re.search(r"event|wedding|cater|photo|dj|flor|אירוע|חתונ|קייטרינג|צלם|די ג'?יי|פרח", text):
        return "events"
    if re.search(r"school|education|kindergarten|child|lesson|course|גן|לימוד|חינוך|צהרון|מורה", text):
        return "education"
    return "general"


def _tagline(category_id: str, city: str) -> str:
    city_label = city or "באזור שלכם"
    taglines = {
        "food": f"טעמים מקומיים ב{city_label} עם חוויה מהירה ונראות שעושה חשק להזמין.",
        "beauty": f"טיפוח וסטייל ב{city_label} עם שירות אישי ונוכחות יוקרתית.",
        "health": f"בריאות, ליווי ושקט מקצועי ב{city_label} עם דגש על בהירות וביטחון.",
        "vehicles": f"שירות רכב ב{city_label} עם שקיפות, זמינות וניהול עבודה מסודר.",
        "repairs": f"פתרון מהיר ומקצועי ב{city_label} עם תקשורת ברורה וביצוע נקי.",
        "events": f"הפקה וניהול אירועים ב{city_label} עם קו יצירתי מוקפד ושליטה בפרטים.",
        "education": f"למידה והתקדמות ב{city_label} עם מסלול ברור, אישי ומקצועי.",
        "general": f"שירות מקומי מוביל ב{city_label} עם נראות פרימיום ומסלול פנייה ברור.",
    }
    return taglines.get(category_id, taglines["general"])


def _reviews_json(raw_reviews: list[dict] | None) -> str | None:
    items = []
    for review in raw_reviews or []:
        text = str(review.get("text") or "").strip()
        if not text:
            continue
        items.append({
            "author_name": review.get("author_name") or review.get("author") or "לקוח/ה",
            "rating": review.get("rating") or 5,
            "text": text,
            "relative_time_description": review.get("relative_time_description") or "",
        })
    return json.dumps(items[:5], ensure_ascii=False) if items else None


def _create_site(db: Session | None, place: dict, category_label: str, fallback_city: str, dry_run: bool) -> bool:
    place_id = str(place.get("place_id") or "").strip()
    if not place_id:
        return False
    if db is not None:
        if db.query(DemoSite.id).filter(DemoSite.place_id == place_id).first():
            return False
        if db.query(Business.id).filter(Business.google_place_id == place_id).first():
            return False

    name = str(place.get("name") or "").strip()
    if not name:
        return False

    address = str(place.get("address") or "").strip()
    city = _extract_city(address, fallback_city)
    types = place.get("types") or []
    category_id = _category_id(category_label, types)
    phone = str(place.get("phone") or "").strip() or None
    website = str(place.get("website") or "").strip() or None
    maps_url = str(place.get("google_maps_url") or f"https://www.google.com/maps/place/?q=place_id:{place_id}").strip()
    photo_url = str(place.get("photo_url") or "").strip() or None
    opening_hours = place.get("opening_hours") or []
    rating = float(place["rating"]) if place.get("rating") is not None else None
    reviews_count = int(place["reviews_count"]) if place.get("reviews_count") else None
    top_review = str(place.get("top_review") or "").strip() or None
    slug = _unique_slug(name, city, place_id, db)

    if dry_run:
        log.info("[DRY-RUN] %s | %s | %s | %s", city, category_id, name, slug)
        return True

    try:
        business = Business(
            name=name,
            city=city,
            category=category_id,
            status="active",
            phone=phone,
            address=address or None,
            google_place_id=place_id,
            lat=place.get("lat"),
            lng=place.get("lng"),
            rating=rating,
            photo_url=photo_url,
            website=website,
        )
        db.add(business)
        db.flush()

        site = DemoSite(
            business_id=business.id,
            slug=slug,
            place_id=place_id,
            business_name=name,
            tagline=_tagline(category_id, city),
            phone=phone,
            address=address or None,
            city=city,
            rating=rating,
            reviews_count=reviews_count,
            google_maps_url=maps_url,
            top_review=top_review,
            business_types=", ".join(types)[:500] if types else category_label,
            category=category_id,
            website=website,
            opening_hours=json.dumps(opening_hours, ensure_ascii=False) if opening_hours else None,
            reviews_json=None,
            photo_url=photo_url,
            status="seeded",
        )
        db.add(site)
        db.commit()
        log.debug("created %s | %s | %s", city, category_id, name)
        return True
    except Exception:
        db.rollback()
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mass-seed demo sites from Google Places.")
    parser.add_argument("--per-combo", type=int, default=6, help="How many businesses to request per city/category combo")
    parser.add_argument("--limit", type=int, default=0, help="Optional hard cap on total newly created sites")
    parser.add_argument("--min-reviews", type=int, default=0, help="Filter out businesses below this review count")
    parser.add_argument("--min-rating", type=float, default=0.0, help="Filter out businesses below this rating")
    parser.add_argument("--no-website-only", action="store_true", help="Prefer businesses without websites")
    parser.add_argument("--cities", type=str, default="", help="Comma-separated city override")
    parser.add_argument("--category", type=str, default="", help="Optional category label filter")
    parser.add_argument("--dry-run", action="store_true", help="List candidates without writing to the DB")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    service = PlacesService()
    db: Session | None = None if args.dry_run else SessionLocal()

    categories = service.get_categories()
    if args.category:
        needle = args.category.strip().lower()
        categories = [item for item in categories if needle in item["label"].lower()]

    cities = [part.strip() for part in args.cities.split(",") if part.strip()] or TARGET_CITIES

    created = 0
    attempted = 0
    try:
        for city in cities:
            for category in categories:
                if args.limit and created >= args.limit:
                    break

                label = category["label"]
                log.info("Searching category='%s' city='%s'", label, city)
                results = service.search_businesses(
                    city=city,
                    category=label,
                    limit=args.per_combo,
                    no_website_only=args.no_website_only,
                    min_reviews=args.min_reviews,
                    min_rating=args.min_rating,
                )

                combo_created = 0
                for place in results:
                    if args.limit and created >= args.limit:
                        break
                    attempted += 1
                    if _create_site(db, place, label, city, args.dry_run):
                        created += 1
                        combo_created += 1

                log.info("→ %s / %s yielded %d new site(s)", city, label, combo_created)

            if args.limit and created >= args.limit:
                break
    finally:
        if db is not None:
            db.close()

    mode = "would create" if args.dry_run else "created"
    log.info("Done: %s %d site(s) across %d attempts.", mode, created, attempted)


if __name__ == "__main__":
    main()