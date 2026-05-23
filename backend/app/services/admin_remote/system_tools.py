"""system_tools.py
==================
TAZO-WEB Tool Library — real-time functions the AI agents can call.

Each tool:
  • Accepts simple parameters (no huge objects)
  • Returns a clean dict  {ok: bool, data: ..., error: str | None}
  • Is side-effect-free (read-only), EXCEPT send_whatsapp which requires
    an explicit PIN gate upstream in the router before it is ever reached.

Tool registry (TOOLS_SCHEMA) follows the OpenAI / xAI / Anthropic
function-calling schema so it can be embedded directly in any API call.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. get_system_stats
# ─────────────────────────────────────────────────────────────────────────────

def get_system_stats(db: Session) -> dict[str, Any]:
    """Return a live snapshot of the TAZO-WEB database: leads, sites, messages."""
    try:
        import datetime as dt
        from sqlalchemy import cast, func
        from sqlalchemy.types import Date
        from app.models.lead_record import LeadRecord
        from app.models.business import Business
        from app.models.outreach_message import OutreachMessage
        from app.models.draft_site import DraftSite

        today = dt.date.today()

        total_leads    = db.query(func.count(LeadRecord.id)).scalar() or 0
        hot_leads      = db.query(func.count(LeadRecord.id)).filter(
            LeadRecord.status.in_(["hot", "super_hot", "boiling_hot"])
        ).scalar() or 0
        boiling        = db.query(func.count(LeadRecord.id)).filter(
            LeadRecord.status == "boiling_hot"
        ).scalar() or 0
        new_today      = db.query(func.count(LeadRecord.id)).filter(
            cast(LeadRecord.created_at, Date) == today
        ).scalar() or 0
        total_biz      = db.query(func.count(Business.id)).scalar() or 0
        total_drafts   = db.query(func.count(DraftSite.id)).scalar() or 0
        sent_today     = db.query(func.count(OutreachMessage.id)).filter(
            cast(OutreachMessage.created_at, Date) == today,
            OutreachMessage.channel == "whatsapp",
        ).scalar() or 0
        replied_today  = db.query(func.count(OutreachMessage.id)).filter(
            cast(OutreachMessage.created_at, Date) == today,
            OutreachMessage.status.in_(["replied", "read"]),
        ).scalar() or 0

        return {
            "ok": True,
            "data": {
                "leads": {
                    "total": total_leads,
                    "hot": hot_leads,
                    "boiling_hot": boiling,
                    "new_today": new_today,
                },
                "sites": {
                    "businesses": total_biz,
                    "drafts": total_drafts,
                },
                "outreach_today": {
                    "sent": sent_today,
                    "replied": replied_today,
                    "reply_rate_pct": round(replied_today / sent_today * 100, 1) if sent_today else 0,
                },
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] get_system_stats failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 2. fetch_lead_details
# ─────────────────────────────────────────────────────────────────────────────

def fetch_lead_details(lead_id: int, db: Session) -> dict[str, Any]:
    """Return full context of a single lead by ID."""
    try:
        from app.models.lead_record import LeadRecord

        lead = db.query(LeadRecord).filter(LeadRecord.id == lead_id).first()
        if not lead:
            return {"ok": False, "data": None, "error": f"Lead {lead_id} not found"}

        return {
            "ok": True,
            "data": {
                "id": lead.id,
                "name": lead.imported_name,
                "phone": lead.phone,
                "city": lead.city,
                "category": lead.category,
                "address": lead.address,
                "website": lead.website_url,
                "score": lead.score,
                "status": lead.status,
                "rating": lead.rating,
                "reviews": lead.reviews_count,
                "facebook": lead.facebook_url,
                "instagram": lead.instagram_url,
                "tiktok": lead.tiktok_url,
                "digital_gap": lead.digital_gap_label,
                "cross_ref_status": lead.cross_ref_status,
                "cross_ref_score": lead.cross_ref_score,
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] fetch_lead_details failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 3. search_business_data
# ─────────────────────────────────────────────────────────────────────────────

def search_business_data(business_name: str, city: str = "") -> dict[str, Any]:
    """Search online for a business using Serper/Google. Returns raw profile data."""
    try:
        import httpx
        from app.core.config import settings

        serper_key = settings.serper_api_key or ""
        if not serper_key:
            return {"ok": False, "data": None, "error": "SERPER_API_KEY not configured"}

        query = f"{business_name} {city}".strip()
        resp = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "il", "hl": "iw", "num": 5},
            timeout=15,
        )
        resp.raise_for_status()
        raw = resp.json()

        results = []
        for item in raw.get("organic", [])[:5]:
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
            })

        knowledge = raw.get("knowledgeGraph", {})

        return {
            "ok": True,
            "data": {
                "query": query,
                "knowledge_graph": {
                    "name": knowledge.get("title"),
                    "type": knowledge.get("type"),
                    "phone": knowledge.get("phoneNumber"),
                    "address": knowledge.get("address"),
                    "website": knowledge.get("website"),
                    "rating": knowledge.get("rating"),
                } if knowledge else None,
                "organic_results": results,
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] search_business_data failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 4. check_domain_availability
# ─────────────────────────────────────────────────────────────────────────────

def check_domain_availability(domain: str) -> dict[str, Any]:
    """Check if a domain name is available via Hostinger API."""
    try:
        from app.services.hostinger_service import HostingerService

        svc = HostingerService()
        if not svc.is_configured():
            return {"ok": False, "data": None, "error": "HOSTINGER_API_TOKEN not configured"}

        available = svc.check_availability(domain)
        return {
            "ok": True,
            "data": {
                "domain": domain,
                "available": available,
                "message": f"✅ {domain} פנוי לרישום" if available else f"❌ {domain} תפוס",
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] check_domain_availability failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 5. get_hot_leads  (top-N with full details)
# ─────────────────────────────────────────────────────────────────────────────

def get_hot_leads(db: Session, limit: int = 10) -> dict[str, Any]:
    """Return the top N hot/boiling leads with full context."""
    try:
        from app.models.lead_record import LeadRecord

        leads = (
            db.query(LeadRecord)
            .filter(LeadRecord.status.in_(["boiling_hot", "super_hot", "hot"]))
            .order_by(LeadRecord.score.desc())
            .limit(limit)
            .all()
        )
        if not leads:
            return {"ok": True, "data": {"leads": [], "count": 0}}

        return {
            "ok": True,
            "data": {
                "count": len(leads),
                "leads": [
                    {
                        "id": l.id,
                        "name": l.imported_name,
                        "phone": l.phone,
                        "city": l.city,
                        "category": l.category,
                        "score": l.score,
                        "status": l.status,
                        "digital_gap": l.digital_gap_label,
                        "facebook": bool(l.facebook_url),
                        "instagram": bool(l.instagram_url),
                        "website": l.website_url,
                    }
                    for l in leads
                ],
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] get_hot_leads failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 6. fetch_facebook_data
# ─────────────────────────────────────────────────────────────────────────────

def fetch_facebook_data(page_id_or_url: str) -> dict[str, Any]:
    """Fetch live Facebook page stats via Meta Graph API: followers, posts, last activity."""
    try:
        import httpx
        import datetime as dt
        from app.core.config import settings

        token = settings.facebook_access_token or ""
        if not token:
            return {"ok": False, "data": None, "error": "FACEBOOK_ACCESS_TOKEN not configured"}

        # Normalise: extract page handle/ID from URL if needed
        page_id = page_id_or_url.strip()
        if "facebook.com/" in page_id:
            page_id = page_id.rstrip("/").split("facebook.com/")[-1].split("?")[0].split("/")[0]

        fields = "name,about,fan_count,website,link,overall_star_rating,rating_count,posts.limit(5){message,created_time}"
        resp = httpx.get(
            f"https://graph.facebook.com/v19.0/{page_id}",
            params={"fields": fields, "access_token": token},
            timeout=12,
        )
        raw = resp.json()

        if "error" in raw:
            return {"ok": False, "data": None, "error": raw["error"].get("message", "Graph API error")}

        # Last post activity
        posts_raw = (raw.get("posts") or {}).get("data", [])
        last_post_date = None
        days_since_last_post = None
        if posts_raw:
            last_post_date = posts_raw[0].get("created_time", "")[:10]
            try:
                delta = dt.date.today() - dt.date.fromisoformat(last_post_date)
                days_since_last_post = delta.days
            except Exception:
                pass

        activity_level = "unknown"
        if days_since_last_post is not None:
            if days_since_last_post <= 7:
                activity_level = "active"
            elif days_since_last_post <= 30:
                activity_level = "moderate"
            elif days_since_last_post <= 180:
                activity_level = "dormant"
            else:
                activity_level = "dead"

        return {
            "ok": True,
            "data": {
                "name": raw.get("name"),
                "about": raw.get("about"),
                "followers": raw.get("fan_count"),
                "website": raw.get("website"),
                "link": raw.get("link"),
                "rating": raw.get("overall_star_rating"),
                "rating_count": raw.get("rating_count"),
                "last_post_date": last_post_date,
                "days_since_last_post": days_since_last_post,
                "activity_level": activity_level,
                "recent_posts": [
                    {"text": p.get("message", "")[:200], "date": p.get("created_time", "")[:10]}
                    for p in posts_raw[:3]
                ],
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] fetch_facebook_data failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 7. run_apify_scraper
# ─────────────────────────────────────────────────────────────────────────────

def run_apify_scraper(target_url: str, platform: str = "instagram") -> dict[str, Any]:
    """
    Trigger an Apify actor to scrape Instagram or TikTok profile content.
    platform: 'instagram' | 'tiktok'
    Returns bio, followers, media URLs (images/covers), last post date.
    """
    try:
        from app.core.config import settings

        token = settings.apify_api_token or ""
        if not token:
            return {"ok": False, "data": None, "error": "APIFY_API_TOKEN not configured"}

        try:
            from apify_client import ApifyClient
        except ImportError:
            return {"ok": False, "data": None, "error": "apify-client package not installed"}

        client = ApifyClient(token)
        platform = platform.lower().strip()

        # Extract username from URL
        username = target_url.rstrip("/").split("/")[-1].lstrip("@").split("?")[0]
        if not username:
            return {"ok": False, "data": None, "error": "Could not extract username from URL"}

        if platform == "instagram":
            run = client.actor("apify/instagram-scraper").call(
                run_input={
                    "usernames": [username],
                    "resultsType": "posts",
                    "resultsLimit": 6,
                    "addParentData": True,
                },
                timeout_secs=60,
                memory_mbytes=256,
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            media_urls = []
            for item in items[:6]:
                url = item.get("displayUrl") or item.get("videoUrl")
                if url:
                    media_urls.append(url)

            # Profile data is in the first item's owner field
            profile_data = {}
            if items:
                owner = items[0].get("ownerUsername") or username
                _followers = items[0].get("likesCount")  # fallback
                profile_data = {
                    "username": owner,
                    "followers": items[0].get("followersCount"),
                    "bio": items[0].get("biography", ""),
                    "post_count": items[0].get("postsCount"),
                }

            return {
                "ok": True,
                "data": {
                    "platform": "instagram",
                    "username": username,
                    "profile": profile_data,
                    "media_urls": media_urls[:6],
                    "posts_scraped": len(items),
                },
            }

        elif platform == "tiktok":
            run = client.actor("clockworks/free-tiktok-scraper").call(
                run_input={
                    "profiles": [f"@{username}"],
                    "resultsPerPage": 5,
                    "shouldDownloadVideos": False,
                    "shouldDownloadCovers": True,
                },
                timeout_secs=90,
                memory_mbytes=256,
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            covers = []
            for item in items[:5]:
                cover = (item.get("videoMeta") or {}).get("coverUrl") or item.get("webVideoUrl")
                if cover:
                    covers.append(cover)

            author_meta = items[0].get("authorMeta", {}) if items else {}
            return {
                "ok": True,
                "data": {
                    "platform": "tiktok",
                    "username": username,
                    "profile": {
                        "username": author_meta.get("name", username),
                        "followers": author_meta.get("fans"),
                        "bio": author_meta.get("signature", ""),
                        "verified": author_meta.get("verified", False),
                    },
                    "media_urls": covers,
                    "posts_scraped": len(items),
                },
            }
        else:
            return {"ok": False, "data": None, "error": f"Unsupported platform: {platform}. Use 'instagram' or 'tiktok'"}

    except Exception as exc:
        logger.exception("[system_tools] run_apify_scraper failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 8. get_google_places_details
# ─────────────────────────────────────────────────────────────────────────────

def get_google_places_details(business_name: str, city: str = "") -> dict[str, Any]:
    """
    Official Google Places lookup — the 'single source of truth' for NAP
    (Name, Address, Phone), rating, reviews, hours and website.
    """
    try:
        from app.services.enrichment.places_service import PlacesService

        svc = PlacesService()
        if not svc.api_key:
            return {"ok": False, "data": None, "error": "GOOGLE_PLACES_API_KEY not configured"}

        results = svc.search_businesses(city=city or "ישראל", category=business_name, limit=3)
        if not results:
            return {"ok": True, "data": {"found": False, "results": []}}

        top = results[0]
        return {
            "ok": True,
            "data": {
                "found": True,
                "top_match": {
                    "name": top.get("name"),
                    "address": top.get("address"),
                    "phone": top.get("phone"),
                    "website": top.get("website"),
                    "rating": top.get("rating"),
                    "reviews_count": top.get("reviews_count"),
                    "status": top.get("status"),
                    "google_maps_url": top.get("google_maps_url"),
                    "opening_hours": top.get("opening_hours", []),
                    "top_review": top.get("top_review"),
                    "place_id": top.get("place_id"),
                    "has_website": bool(top.get("website")),
                },
                "other_matches": [
                    {"name": r.get("name"), "address": r.get("address"), "rating": r.get("rating")}
                    for r in results[1:3]
                ],
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] get_google_places_details failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 9. crawl_existing_website
# ─────────────────────────────────────────────────────────────────────────────

def crawl_existing_website(url: str) -> dict[str, Any]:
    """
    Fetch and analyse a business website to understand their existing services,
    copy quality, mobile readiness, and contact info — so we can build a better one.
    """
    try:
        import httpx
        import re

        if not url.startswith("http"):
            url = "https://" + url

        resp = httpx.get(
            url,
            timeout=12,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Mobile Safari/537.36"
                )
            },
        )
        html = resp.text
        final_url = str(resp.url)

        # Title
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        page_title = title_m.group(1).strip()[:120] if title_m else ""

        # Meta description
        meta_m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{0,300})', html, re.IGNORECASE)
        if not meta_m:
            meta_m = re.search(r'<meta[^>]+content=["\']([^"\']{0,300})[^>]+name=["\']description["\']', html, re.IGNORECASE)
        meta_desc = meta_m.group(1).strip() if meta_m else ""

        # Headings (h1 + h2)
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.IGNORECASE | re.DOTALL)
        clean_tag = re.compile(r"<[^>]+>")
        headings = [clean_tag.sub("", h).strip()[:100] for h in (h1s[:2] + h2s[:4]) if h.strip()]

        # Contact info
        phone_m = re.search(r"(?:0[235789]\d[-\s]?\d{3}[-\s]?\d{4}|0[235789]\d{7,8})", html)
        phone = phone_m.group(0) if phone_m else ""
        email_m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
        email = email_m.group(0) if email_m else ""

        # Mobile friendliness signals
        has_viewport = bool(re.search(r'name=["\']viewport["\']', html, re.IGNORECASE))
        is_wordpress = "wp-content" in html or "WordPress" in html
        uses_elementor = "elementor" in html.lower()

        # Approx word count of visible text (very rough)
        stripped = clean_tag.sub(" ", html)
        word_count = len(stripped.split())

        # Social links found on site
        fb_m = re.search(r'https?://(?:www\.)?facebook\.com/([A-Za-z0-9_.]+)', html)
        ig_m = re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)', html)

        return {
            "ok": True,
            "data": {
                "url": final_url,
                "page_title": page_title,
                "meta_description": meta_desc,
                "headings": headings,
                "phone_found": phone,
                "email_found": email,
                "has_mobile_viewport": has_viewport,
                "is_wordpress": is_wordpress,
                "uses_elementor": uses_elementor,
                "approx_word_count": word_count,
                "facebook_link": fb_m.group(0) if fb_m else None,
                "instagram_link": ig_m.group(0) if ig_m else None,
                "assessment": (
                    "אין מטא-תג viewport — האתר כנראה לא מותאם לנייד" if not has_viewport
                    else "יש viewport — ייתכן שמותאם לנייד"
                ),
            },
        }
    except Exception as exc:
        logger.exception("[system_tools] crawl_existing_website failed")
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Tool dispatcher — called by the router with function name + args
# ─────────────────────────────────────────────────────────────────────────────

TOOL_NAMES = {
    "get_system_stats",
    "fetch_lead_details",
    "search_business_data",
    "check_domain_availability",
    "get_hot_leads",
    "fetch_facebook_data",
    "run_apify_scraper",
    "get_google_places_details",
    "crawl_existing_website",
}


def dispatch_tool(tool_name: str, args: dict, db: Session | None = None) -> dict[str, Any]:
    """Execute a tool by name with the given args. Returns tool result dict."""
    if tool_name not in TOOL_NAMES:
        return {"ok": False, "data": None, "error": f"Unknown tool: {tool_name}"}

    try:
        if tool_name == "get_system_stats":
            return get_system_stats(db)
        elif tool_name == "fetch_lead_details":
            return fetch_lead_details(int(args.get("lead_id", 0)), db)
        elif tool_name == "search_business_data":
            return search_business_data(args.get("business_name", ""), args.get("city", ""))
        elif tool_name == "check_domain_availability":
            return check_domain_availability(args.get("domain", ""))
        elif tool_name == "get_hot_leads":
            return get_hot_leads(db, int(args.get("limit", 10)))
        elif tool_name == "fetch_facebook_data":
            return fetch_facebook_data(args.get("page_id_or_url", ""))
        elif tool_name == "run_apify_scraper":
            return run_apify_scraper(args.get("target_url", ""), args.get("platform", "instagram"))
        elif tool_name == "get_google_places_details":
            return get_google_places_details(args.get("business_name", ""), args.get("city", ""))
        elif tool_name == "crawl_existing_website":
            return crawl_existing_website(args.get("url", ""))
    except Exception as exc:
        logger.exception("[system_tools] dispatch_tool(%s) failed", tool_name)
        return {"ok": False, "data": None, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI / xAI / Anthropic-compatible tool schema
# ─────────────────────────────────────────────────────────────────────────────

TOOLS_SCHEMA: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_system_stats",
            "description": (
                "שלוף נתונים חיים ממסד הנתונים של TAZO-WEB: "
                "כמות לידים, אתרים, הודעות WhatsApp. "
                "השתמש כשנשאלת על מצב המערכת, KPIs, ביצועים יומיים."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_lead_details",
            "description": (
                "קבל את כל הפרטים של ליד ספציפי לפי מזהה (ID). "
                "השתמש כשמבקשים מידע על ליד מסוים."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "integer",
                        "description": "ה-ID של הליד במסד הנתונים",
                    }
                },
                "required": ["lead_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_business_data",
            "description": (
                "חפש מידע על עסק ברשת (Serper/Google). "
                "משתמשים כשצריך מידע OSINT על עסק: טלפון, כתובת, אתר, רייטינג."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "business_name": {
                        "type": "string",
                        "description": "שם העסק לחיפוש",
                    },
                    "city": {
                        "type": "string",
                        "description": "עיר (אופציונלי, לצמצום התוצאות)",
                    },
                },
                "required": ["business_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_domain_availability",
            "description": (
                "בדוק אם דומיין מסוים פנוי לרישום דרך Hostinger. "
                "השתמש כשמבקשים לבדוק אם שם דומיין זמין."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "שם הדומיין לבדיקה, למשל: example.co.il",
                    }
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hot_leads",
            "description": (
                "קבל רשימת הלידים החמים ביותר במערכת עם פרטים מלאים. "
                "השתמש כשמבקשים 'מי הלידים הכי חמים' או 'איזה עסקים להתחיל איתם'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "כמות הלידים להחזיר (ברירת מחדל: 10)",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_facebook_data",
            "description": (
                "שלוף נתונים חיים מדף פייסבוק של עסק: עוקבים, פוסטים אחרונים, "
                "רמת פעילות (active/dormant/dead), רייטינג. "
                "השתמש כשצריך לנתח את הנוכחות הדיגיטלית של לקוח פוטנציאלי בפייסבוק."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "URL של דף הפייסבוק או Page ID, למשל: https://facebook.com/pizza-don-lowe או '123456789'",
                    }
                },
                "required": ["page_id_or_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_apify_scraper",
            "description": (
                "הפעל Apify actor לגריידה עמוקה של אינסטגרם או טיקטוק: "
                "תמונות, סרטונים, ביו, כמות עוקבים. "
                "השתמש כשצריך תוכן ויזואלי לאתר או ניתוח מעמיק של הפרזנציה הסושיאל."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {
                        "type": "string",
                        "description": "URL הפרופיל, למשל: https://instagram.com/pizza_don_lowe",
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["instagram", "tiktok"],
                        "description": "הפלטפורמה: 'instagram' או 'tiktok'",
                    },
                },
                "required": ["target_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_google_places_details",
            "description": (
                "שלוף את הנתונים הרשמיים של עסק מ-Google Places: "
                "טלפון, כתובת, שעות פתיחה, רייטינג, ביקורות — מקור האמת (NAP). "
                "השתמש לכל בדיקת נוכחות גוגל של ליד חדש."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "business_name": {
                        "type": "string",
                        "description": "שם העסק לחיפוש בגוגל מאפס",
                    },
                    "city": {
                        "type": "string",
                        "description": "עיר (אופציונלי, מגביר דיוק)",
                    },
                },
                "required": ["business_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crawl_existing_website",
            "description": (
                "גרד ונתח את האתר הקיים של עסק: כותרות, תיאור, טלפון, אימייל, "
                "האם מותאם לנייד, האם WordPress, מה השירותים המוזכרים. "
                "השתמש לפני בניית אתר חדש — כדי להבין מה לשפר."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "כתובת האתר לגרידה, למשל: https://old-site.co.il",
                    }
                },
                "required": ["url"],
            },
        },
    },
]

# Anthropic-format tools (slightly different schema)
TOOLS_SCHEMA_ANTHROPIC: list[dict] = [
    {
        "name": t["function"]["name"],
        "description": t["function"]["description"],
        "input_schema": t["function"]["parameters"],
    }
    for t in TOOLS_SCHEMA
]
