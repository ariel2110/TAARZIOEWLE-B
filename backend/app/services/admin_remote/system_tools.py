"""system_tools.py
==================
SiteNest Tool Library — real-time functions the AI agents can call.

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
    """Return a live snapshot of the SiteNest database: leads, sites, messages."""
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
# Tool dispatcher — called by the router with function name + args
# ─────────────────────────────────────────────────────────────────────────────

TOOL_NAMES = {
    "get_system_stats",
    "fetch_lead_details",
    "search_business_data",
    "check_domain_availability",
    "get_hot_leads",
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
                "שלוף נתונים חיים ממסד הנתונים של SiteNest: "
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
