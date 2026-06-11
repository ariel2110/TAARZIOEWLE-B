"""
Google Places API enrichment service.
Optimized for discovering small local businesses WITHOUT websites —
the best leads for site-building services.
"""
from __future__ import annotations

import httpx
import logging
import time
from typing import Any
from app.core.config import settings

logger = logging.getLogger(__name__)

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL     = "https://maps.googleapis.com/maps/api/place/details/json"
PLACES_PHOTO_URL       = "https://maps.googleapis.com/maps/api/place/photo"

DETAIL_FIELDS = (
    "name,formatted_address,formatted_phone_number,international_phone_number,"
    "website,rating,user_ratings_total,opening_hours,business_status,"
    "url,vicinity,types,reviews,place_id,geometry,photos"
)

# Each entry: label (Hebrew display), queries (Hebrew search phrases)
SMALL_BIZ_CATEGORIES: list[dict] = [
    {"label": "מספרה / ספרות", "queries": ["מספרה", "ספרות שיער", "תספורת"]},
    {"label": "מוסך / מכונאות", "queries": ["מוסך", "מכונאות רכב", "תיקון רכב"]},
    {"label": "גנן / גינון", "queries": ["גנן", "גינון ועיצוב גינות", "שירותי גינון"]},
    {"label": "שרברב / אינסטלציה", "queries": ["שרברב", "אינסטלציה", "תיקון צנרת"]},
    {"label": "חשמלאי", "queries": ["חשמלאי", "שירותי חשמל"]},
    {"label": "טכנאי מזגנים", "queries": ["טכנאי מזגנים", "התקנת מזגן", "מזגנים תיקון"]},
    {"label": "שיפוצניק / קבלן", "queries": ["שיפוצניק", "קבלן שיפוצים", "גבס ושיפוצים"]},
    {"label": "ניקיון", "queries": ["חברת ניקיון", "שירותי ניקיון", "ניקיון בתים"]},
    {"label": "מכון יופי / ספא", "queries": ["מכון יופי", "ספא", "טיפולי פנים"]},
    {"label": "ציפורניים / מניקור", "queries": ["מניקור פדיקור", "ציפורניים ג'ל", "נייל ארט"]},
    {"label": "גריל / שיפודייה", "queries": ["שיפודייה", "גריל ומנגל", "מסעדת בשר"]},
    {"label": "פיצרייה", "queries": ["פיצרייה", "פיצה"]},
    {"label": "בית קפה", "queries": ["בית קפה", "קפה עצמאי"]},
    {"label": "מאפייה / פתיסרי", "queries": ["מאפייה", "פתיסרי", "עוגות ומאפים"]},
    {"label": "וטרינר", "queries": ["וטרינר", "מרפאה וטרינרית", "קליניקה לחיות"]},
    {"label": "פיזיותרפיה", "queries": ["פיזיותרפיה", "קליניקת פיזיותרפיה"]},
    {"label": "יוגה / פילאטיס", "queries": ["סטודיו יוגה", "פילאטיס", "יוגה"]},
    {"label": "מכבסה / ניקוי יבש", "queries": ["מכבסה", "ניקוי יבש"]},
    {"label": "גן ילדים / צהרון", "queries": ["גן ילדים", "צהרון", "חוגי ילדים"]},
    {"label": "חנות פרחים", "queries": ["חנות פרחים", "פרחים"]},
    {"label": "כל עסקים קטנים", "queries": ["עסק קטן מקומי", "שירות מקומי"]},
]

CATEGORY_QUERY_MAP = {cat["label"]: cat["queries"] for cat in SMALL_BIZ_CATEGORIES}


class PlacesService:
    def __init__(self) -> None:
        self.api_key = settings.google_places_api_key

    def search_businesses(
        self,
        city: str,
        category: str = "",
        limit: int = 50,
        no_website_only: bool = False,
        min_reviews: int = 0,
        min_rating: float = 0.0,
    ) -> list[dict]:
        if not self.api_key:
            return self._demo_dataset(city, category, limit, no_website_only, min_reviews, min_rating)

        queries = self._build_queries(city, category)
        fetch_limit = limit * 3 if no_website_only else limit + 10

        seen_ids: set[str] = set()
        raw_results: list[dict] = []
        for query in queries:
            if len(raw_results) >= fetch_limit:
                break
            batch = self._text_search_all(query, fetch_limit - len(raw_results))
            for place in batch:
                pid = place.get("place_id", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    raw_results.append(place)

        enriched: list[dict] = []
        for place in raw_results:
            detail = self._get_place_detail(place.get("place_id", ""))
            enriched.append(self._normalize(detail or place))

        enriched = self._apply_filters(enriched, no_website_only, min_reviews, min_rating)

        # Sort: no-website first (best leads), then by review count desc
        enriched.sort(key=lambda b: (
            1 if not b.get("website") else 0,
            b.get("reviews_count") or 0,
        ), reverse=True)

        return enriched[:limit]

    def enrich_single(self, place_id: str) -> dict | None:
        if not self.api_key:
            return None
        raw = self._get_place_detail(place_id)
        return self._normalize(raw) if raw else None

    def get_categories(self) -> list[dict]:
        return SMALL_BIZ_CATEGORIES

    # ------------------------------------------------------------------
    def _build_queries(self, city: str, category: str) -> list[str]:
        if category in CATEGORY_QUERY_MAP:
            return [f"{q} {city}" for q in CATEGORY_QUERY_MAP[category]]
        if category:
            return [f"{category} {city}", f"שירות {category} {city}"]
        return [
            f"עסק קטן מקומי {city}",
            f"מספרות {city}",
            f"מוסכים {city}",
            f"בתי קפה {city}",
        ]

    def _text_search_all(self, query: str, limit: int, language: str = "he", region: str = "il") -> list[dict]:
        results: list[dict] = []
        language = "en" if language == "en" else "he"
        region = (region or "il").lower()
        params: dict[str, Any] = {
            "query": query,
            "key": self.api_key,
            "language": language,
            "region": region,
        }
        while len(results) < limit:
            try:
                resp = httpx.get(PLACES_TEXT_SEARCH_URL, params=params, timeout=10)
                data = resp.json()
            except Exception as e:
                logger.warning("Places text search error '%s': %s", query, e)
                break
            results.extend(data.get("results", []))
            next_token = data.get("next_page_token")
            if not next_token or len(results) >= limit:
                break
            time.sleep(2)
            params = {"pagetoken": next_token, "key": self.api_key}
        return results[:limit]

    def _get_place_detail(self, place_id: str, language: str = "he") -> dict | None:
        if not place_id:
            return None
        language = "en" if language == "en" else "he"
        try:
            resp = httpx.get(
                PLACES_DETAILS_URL,
                params={"place_id": place_id, "fields": DETAIL_FIELDS, "key": self.api_key, "language": language},
                timeout=10,
            )
            return resp.json().get("result")
        except Exception as e:
            logger.warning("Places detail error %s: %s", place_id, e)
            return None

    def _normalize(self, raw: dict) -> dict:
        reviews = raw.get("reviews") or []
        top_review = reviews[0].get("text", "") if reviews else ""
        geo = (raw.get("geometry") or {}).get("location", {})
        photos = raw.get("photos") or []
        photo_ref = photos[0].get("photo_reference") if photos else ""
        return {
            "name":            raw.get("name", ""),
            "address":         raw.get("formatted_address") or raw.get("vicinity", ""),
            "phone":           raw.get("formatted_phone_number") or raw.get("international_phone_number", ""),
            "website":         raw.get("website", ""),
            "rating":          raw.get("rating"),
            "reviews_count":   raw.get("user_ratings_total"),
            "google_maps_url": raw.get("url", ""),
            "status":          raw.get("business_status", ""),
            "types":           raw.get("types", []),
            "top_review":      top_review,
            "opening_hours":   (raw.get("opening_hours") or {}).get("weekday_text", []),
            "place_id":        raw.get("place_id", ""),
            "lat":             geo.get("lat"),
            "lng":             geo.get("lng"),
            "photo_url":       f"{PLACES_PHOTO_URL}?maxwidth=1200&photo_reference={photo_ref}&key={self.api_key}" if photo_ref and self.api_key else "",
        }

    def _apply_filters(
        self,
        businesses: list[dict],
        no_website_only: bool,
        min_reviews: int,
        min_rating: float,
    ) -> list[dict]:
        out = []
        for b in businesses:
            if no_website_only and b.get("website"):
                continue
            if min_reviews and (b.get("reviews_count") or 0) < min_reviews:
                continue
            if min_rating and (b.get("rating") or 0.0) < min_rating:
                continue
            out.append(b)
        return out

    # ------------------------------------------------------------------
    def _demo_dataset(self, city, category, limit, no_website_only, min_reviews, min_rating):
        base = [
            {"name": "מספרת שיק", "address": "רחוב הרצל 22, תל אביב", "phone": "03-5190011", "website": "", "rating": 4.3, "reviews_count": 148, "types": ["hair_care", "beauty_salon"], "status": "OPERATIONAL", "place_id": "demo_009"},
            {"name": "מוסך טוטל קאר", "address": "רחוב חיים לבנון 50, תל אביב", "phone": "03-6455566", "website": "", "rating": 4.3, "reviews_count": 123, "types": ["car_repair"], "status": "OPERATIONAL", "place_id": "demo_023"},
            {"name": "מסעדת שווארמה מלך", "address": "רחוב הגדוד העברי 6, תל אביב", "phone": "03-5183344", "website": "", "rating": 4.5, "reviews_count": 678, "types": ["restaurant", "food"], "status": "OPERATIONAL", "place_id": "demo_035"},
            {"name": "מרפאת וטרינר נאמן", "address": "רחוב מסריק 4, תל אביב", "phone": "03-6041122", "website": "", "rating": 4.8, "reviews_count": 219, "types": ["veterinary_care"], "status": "OPERATIONAL", "place_id": "demo_033"},
            {"name": "מאפיית לחמי", "address": "שוק לוינסקי, תל אביב", "phone": "03-5189001", "website": "", "rating": 4.7, "reviews_count": 445, "types": ["bakery", "food"], "status": "OPERATIONAL", "place_id": "demo_019"},
            {"name": "מכון ציפורניים נאיה", "address": "רחוב קינג ג'ורג' 90, תל אביב", "phone": "054-4567890", "website": "", "rating": 4.6, "reviews_count": 267, "types": ["beauty_salon", "nail_salon"], "status": "OPERATIONAL", "place_id": "demo_012"},
            {"name": "גלידריית GELATO MARE", "address": "שדרות בן גוריון 18, תל אביב", "phone": "03-5201234", "website": "", "rating": 4.8, "reviews_count": 558, "types": ["ice_cream_shop"], "status": "OPERATIONAL", "place_id": "demo_029"},
            {"name": "בר קוקטיילים SECRET", "address": "רחוב לילנבלום 14, תל אביב", "phone": "054-9988770", "website": "", "rating": 4.7, "reviews_count": 423, "types": ["bar"], "status": "OPERATIONAL", "place_id": "demo_041"},
            {"name": "קפה נמרוד", "address": "רחוב דיזנגוף 100, תל אביב", "phone": "03-5221100", "website": "https://cafenimrod.co.il", "rating": 4.5, "reviews_count": 312, "types": ["cafe"], "status": "OPERATIONAL", "place_id": "demo_001"},
            {"name": "מכון כושר פלאפיט", "address": "רחוב הארבעה 19, תל אביב", "phone": "03-6248800", "website": "https://flafit.co.il", "rating": 4.7, "reviews_count": 541, "types": ["gym"], "status": "OPERATIONAL", "place_id": "demo_004"},
        ]
        rows = [dict(b, google_maps_url="", top_review="", opening_hours=[], photo_url="") for b in base]
        if category:
            matched = [b for b in rows if any(category.lower() in t for t in b.get("types", []))]
            rows = matched or rows
        return self._apply_filters(rows, no_website_only, min_reviews, min_rating)[:limit]
