#!/usr/bin/env python3
"""
seed_demo_sites.py
------------------
Seed the demo_sites table with ~1000 Israeli businesses from Google Places API.
Run inside the backend container:
    docker exec localbiz-backend python3 scripts/seed_demo_sites.py

Requires: GOOGLE_PLACES_API_KEY in environment / .env
"""

import os, sys, re, time, unicodedata, logging, asyncio
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import httpx
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.business import Business
from app.models.demo_site import DemoSite

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("seeder")

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_URL   = "https://maps.googleapis.com/maps/api/place/photo"

TARGET = 1000   # target total demo sites created

# Categories → (Google search keyword, internal category_id)
SEARCHES = [
    ("מסעדה", "food"),
    ("פיצריה", "food"),
    ("קפה", "food"),
    ("שוורמה", "food"),
    ("המבורגר", "food"),
    ("ספר", "beauty"),
    ("מספרה", "beauty"),
    ("ציפורניים מניקור", "beauty"),
    ("קוסמטיקה", "beauty"),
    ("עיסוי ספא", "beauty"),
    ("חשמלאי", "repairs"),
    ("שרברב", "repairs"),
    ("מזגנים", "repairs"),
    ("שיפוצניק", "repairs"),
    ("נגר", "repairs"),
    ("מוסך", "vehicles"),
    ("צמיגייה", "vehicles"),
    ("שטיפת רכבים", "vehicles"),
    ("ביטוח רכב", "vehicles"),
    ("חלקי חילוף לרכב", "vehicles"),
    ("אולם אירועים", "events"),
    ("צלם אירועים", "events"),
    ("קייטרינג", "events"),
    ("די ג'יי", "events"),
    ("מדריך כושר", "health"),
    ("חדר כושר", "health"),
    ("פיזיותרפיה", "health"),
    ("רופא שיניים", "health"),
    ("אופטיקה", "health"),
]

CITIES = [
    "תל אביב", "ירושלים", "חיפה", "באר שבע", "ראשון לציון",
    "נתניה", "פתח תקווה", "אשדוד", "רחובות", "חולון",
    "בני ברק", "רמת גן", "אשקלון", "הרצליה", "כפר סבא",
]


def slugify(name: str) -> str:
    base = unicodedata.normalize("NFKD", name or "biz").encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:40] or "biz"
    return base


def unique_slug(name: str, db: Session) -> str:
    base = slugify(name)
    slug = base
    n = 0
    while db.query(DemoSite).filter(DemoSite.slug == slug).first():
        n += 1
        slug = f"{base}-{n}"
    return slug


def fetch_photo_url(photo_ref: str) -> str | None:
    try:
        r = httpx.get(
            PHOTO_URL,
            params={"maxwidth": 800, "photo_reference": photo_ref, "key": API_KEY},
            follow_redirects=True,
            timeout=10,
        )
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            return str(r.url)
    except Exception as e:
        log.debug(f"photo error: {e}")
    return None


def places_search(keyword: str, city: str, page_token: str | None = None) -> dict:
    params: dict = {"query": f"{keyword} {city}", "key": API_KEY, "language": "iw"}
    if page_token:
        params["pagetoken"] = page_token
    r = httpx.get(PLACES_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def create_demo_site(place: dict, category_id: str, db: Session) -> bool:
    """Create Business + DemoSite for a Google place. Returns True if created."""
    place_id = place.get("place_id")
    if not place_id:
        return False

    # Skip if already seeded
    existing = db.query(DemoSite).join(Business).filter(Business.google_place_id == place_id).first()
    if existing:
        return False

    name    = place.get("name", "")
    address = place.get("formatted_address") or place.get("vicinity") or ""
    lat     = place.get("geometry", {}).get("location", {}).get("lat")
    lng     = place.get("geometry", {}).get("location", {}).get("lng")
    rating  = place.get("rating")

    # Photo
    photo_url = None
    photos = place.get("photos", [])
    if photos:
        photo_url = fetch_photo_url(photos[0]["photo_reference"])

    # Create Business
    biz = Business(
        name=name,
        address=address,
        category=category_id,
        google_place_id=place_id,
        lat=lat,
        lng=lng,
        rating=rating,
        phone=place.get("formatted_phone_number"),
        website=place.get("website"),
        google_maps_url=place.get("url") or f"https://www.google.com/maps/place/?q=place_id:{place_id}",
        photo_url=photo_url,
        status="active",
    )
    db.add(biz)
    db.flush()  # get biz.id

    # Create DemoSite
    slug = unique_slug(name, db)
    site = DemoSite(
        business_id=biz.id,
        slug=slug,
        status="seeded",
        category=category_id,
        photo_url=photo_url,
        google_maps_url=biz.google_maps_url,
    )
    db.add(site)
    db.commit()
    log.info(f"  ✅ {name} → {slug}.tazo-web.com")
    return True


def main():
    if not API_KEY:
        log.error("GOOGLE_PLACES_API_KEY is not set. Aborting.")
        sys.exit(1)

    db = SessionLocal()
    created = 0

    try:
        for city in CITIES:
            if created >= TARGET:
                break
            for keyword, cat_id in SEARCHES:
                if created >= TARGET:
                    break
                log.info(f"Searching: '{keyword}' in {city} ...")
                page_token = None
                for _page in range(3):   # up to 3 pages × 20 results = 60 per combo
                    if created >= TARGET:
                        break
                    try:
                        if page_token:
                            time.sleep(2)   # Google requires a short delay before next_page_token
                        data = places_search(keyword, city, page_token)
                    except Exception as e:
                        log.warning(f"  API error: {e}")
                        break

                    for place in data.get("results", []):
                        if created >= TARGET:
                            break
                        ok = create_demo_site(place, cat_id, db)
                        if ok:
                            created += 1

                    page_token = data.get("next_page_token")
                    if not page_token:
                        break

                log.info(f"  → Total so far: {created}/{TARGET}")
    finally:
        db.close()

    log.info(f"\n🎉 Done! Created {created} demo sites in demo_sites table.")


if __name__ == "__main__":
    main()
