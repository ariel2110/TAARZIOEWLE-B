"""AutoSite Multi-Agent Generation Pipeline
==========================================
Three specialized AI agents collaborate to turn raw Google Maps data
into a beautiful, conversion-focused Hebrew landing page.

  Stage 1 │ Gemini 1.5 Flash  │ Intelligence Analyst
           │                   │ Raw data → structured business intel
  Stage 2 │ GPT-4o            │ Brand Strategist & Hebrew Copywriter
           │                   │ Business intel → marketing copy bundle
  Stage 3 │ Claude 3.5 Sonnet │ Senior Frontend Developer
           │                   │ Copy + design brief → full Tailwind HTML
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Typed data contracts between agents ──────────────────────────────────────

@dataclass
class BusinessIntelReport:
    """Output of Stage 1 (Gemini): objective intelligence extracted from raw Maps data."""
    business_name: str = ""
    business_type: str = ""          # e.g. "חשמלאי", "מסעדה", "כושר"
    city: str = ""
    phone: str = ""
    rating: float | None = None
    reviews_count: int = 0
    review_highlights: list[str] = field(default_factory=list)  # top 3 phrases from reviews
    unique_selling_points: list[str] = field(default_factory=list)
    opening_hours_summary: str = ""  # e.g. "פתוח 24/7" or "א׳-ה׳ 8:00–20:00"
    target_audience: str = ""        # who typically uses this business
    address: str = ""
    website: str = ""


@dataclass
class MarketingCopyBundle:
    """Output of Stage 2 (GPT-4o): complete Hebrew marketing copy for the website."""
    business_name: str = ""
    hero_headline: str = ""          # catchy main headline (≤ 10 words)
    hero_subheadline: str = ""       # short descriptive sentence
    about_us: str = ""               # 2-3 sentence paragraph based on reviews
    services: list[str] = field(default_factory=list)   # 3-6 bullet items
    contact_phone: str = ""
    call_to_action: str = ""         # CTA button text
    tagline: str = ""                # 4-6 word slogan
    brand_personality: str = ""      # e.g. "אמין ומקצועי", "חם ואישי"
    color_scheme: str = "blue"       # "blue" | "orange" | "green" | "purple" | "red"


# ── Stage system prompts ──────────────────────────────────────────────────────

_STAGE1_SYSTEM = """\
אתה אנליסט נתונים עסקיים מומחה. תפקידך לקרוא נתוני גוגל מפות ולחלץ מהם מידע עסקי מובנה.
כללים:
1. אל תמציא מידע — רק מה שמופיע בנתונים.
2. החזר JSON תקין בלבד, ללא שום טקסט נוסף.
3. השתמש בעברית לכל שדות הטקסט.

מבנה JSON נדרש:
{
  "business_name": "שם העסק",
  "business_type": "סוג העסק (מילה אחת או שתיים בעברית)",
  "city": "עיר",
  "phone": "טלפון",
  "rating": 4.8,
  "reviews_count": 120,
  "review_highlights": ["ביטוי חיובי 1", "ביטוי חיובי 2", "ביטוי חיובי 3"],
  "unique_selling_points": ["יתרון 1", "יתרון 2"],
  "opening_hours_summary": "שעות פתיחה קצרות",
  "target_audience": "קהל יעד",
  "address": "כתובת מלאה",
  "website": "כתובת אתר אם קיימת"
}"""

_STAGE2_SYSTEM = """\
אתה אסטרטג מותג ועורך תוכן שיווקי ישראלי מנוסה, המתמחה בקופי שיווקי ממיר בעברית.
תפקידך: לקחת תובנות עסקיות ולהפוך אותן לקופי שיווקי מוביל שיגרום ללקוחות לפנות לעסק.
כללים:
1. כתוב בעברית לאומית, ישירה ונלהבת — לא משרדית.
2. hero_headline — כותרת קצרה ועוצמתית (עד 10 מילים), שמדברת על תוצאה ללקוח.
3. color_scheme — בחר אחד מ: "blue", "orange", "green", "purple", "red", "teal" בהתאם לסוג העסק.
4. החזר JSON תקין בלבד.

מבנה JSON נדרש:
{
  "business_name": "שם העסק",
  "hero_headline": "כותרת ראשית ממירה",
  "hero_subheadline": "משפט תיאורי קצר",
  "about_us": "פסקת אודות (2-3 משפטים בעברית)",
  "services": ["שירות 1", "שירות 2", "שירות 3", "שירות 4"],
  "contact_phone": "טלפון",
  "call_to_action": "טקסט כפתור CTA",
  "tagline": "סלוגן קצר",
  "brand_personality": "אישיות המותג",
  "color_scheme": "blue"
}"""

_STAGE3_SYSTEM = """\
אתה מפתח Frontend בכיר, מומחה בבניית דפי נחיתה מגבירי המרות עם Tailwind CSS.
תפקידך: לבנות דף נחיתה RTL מושלם לעסק ישראלי על בסיס הקופי שיתקבל.
כללים בלתי ניתנים לשינוי:
1. השתמש ב-HTML5 + Tailwind CSS CDN בלבד (<script src="https://cdn.tailwindcss.com"></script>).
2. הדף חייב להיות RTL מלא (dir="rtl" על ה-<html>).
3. Google Fonts — טען את גופן "Heebo" (מתאים לעברית מודרנית).
4. מבנה הדף חייב לכלול: Hero ➝ Services ➝ About ➝ Reviews ➝ Contact ➝ Footer.
5. כפתור פניה צף בפינה (WhatsApp ירוק) — קישור ל-wa.me/{phone}.
6. עיצוב מודרני עם גרדיאנטים, cardsעם צל, כפתורים מעוגלים.
7. פלט: HTML תקני בלבד. אל תוסיף ```html``` או שום טקסט מסביב. התחל עם <!DOCTYPE html> וסיים עם </html>.\
"""


# ── Color scheme → Tailwind tokens ──────────────────────────────────────────

_COLOR_TOKENS: dict[str, dict[str, str]] = {
    "blue":   {"primary": "blue-700",   "light": "blue-50",   "grad_from": "blue-900",   "grad_to": "blue-600",   "btn": "bg-blue-700 hover:bg-blue-800"},
    "orange": {"primary": "orange-600", "light": "orange-50", "grad_from": "orange-900", "grad_to": "orange-500", "btn": "bg-orange-600 hover:bg-orange-700"},
    "green":  {"primary": "green-700",  "light": "green-50",  "grad_from": "green-900",  "grad_to": "green-600",  "btn": "bg-green-700 hover:bg-green-800"},
    "purple": {"primary": "purple-700", "light": "purple-50", "grad_from": "purple-900", "grad_to": "purple-600", "btn": "bg-purple-700 hover:bg-purple-800"},
    "red":    {"primary": "red-700",    "light": "red-50",    "grad_from": "red-900",    "grad_to": "red-600",    "btn": "bg-red-700 hover:bg-red-800"},
    "teal":   {"primary": "teal-700",   "light": "teal-50",   "grad_from": "teal-900",   "grad_to": "teal-600",   "btn": "bg-teal-700 hover:bg-teal-800"},
}


def _clean_phone(phone: str) -> str:
    """Return digits-only phone, adding 972 prefix if needed."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("0") and len(digits) == 10:
        digits = "972" + digits[1:]
    return digits


def _parse_json(raw: str) -> dict | None:
    """Extract first JSON object from a string (strips markdown fences)."""
    if not raw:
        return None
    text = raw.strip()
    # Strip code fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    # Find first { ... }
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


# ── Main pipeline service ─────────────────────────────────────────────────────

class AutoSitePipelineService:
    """
    Orchestrates the 3-stage multi-agent pipeline.
    Usage:
        html = AutoSitePipelineService().run(raw_maps_data)
    Returns full HTML string, or None if pipeline cannot complete.
    """

    def run(self, raw_maps_data: str) -> str | None:
        logger.info("[Pipeline] Starting 3-stage AutoSite generation")
        try:
            intel = self._stage1_analyze(raw_maps_data)
            if not intel:
                logger.warning("[Pipeline] Stage 1 failed, aborting")
                return None
            logger.info("[Pipeline] Stage 1 ✓ business=%s type=%s", intel.business_name, intel.business_type)

            copy = self._stage2_copywrite(intel)
            if not copy:
                logger.warning("[Pipeline] Stage 2 failed, aborting")
                return None
            logger.info("[Pipeline] Stage 2 ✓ headline=%s", copy.hero_headline)

            html = self._stage3_build_html(copy)
            if not html:
                logger.warning("[Pipeline] Stage 3 failed, aborting")
                return None
            logger.info("[Pipeline] Stage 3 ✓ HTML generated (%d bytes)", len(html))
            return html
        except Exception:
            logger.exception("[Pipeline] Unhandled error")
            return None

    # ── Stage 1: Gemini — Intelligence Analyst ───────────────────────────────

    def _stage1_analyze(self, raw: str) -> BusinessIntelReport | None:
        from app.services.llm.router_service import LLMRouterService
        logger.info("[Stage 1] Gemini Intelligence Analyst — parsing business data")
        response = LLMRouterService().call(
            "analyze_business_data",
            f"נתוני גוגל מפות:\n{raw}",
            system=_STAGE1_SYSTEM,
            model="gemini-2.0-flash",
            max_tokens=800,
            json_mode=True,   # enforced when falling back to OpenAI
        )
        data = _parse_json(response or "")
        if not data:
            logger.warning("[Stage 1] Could not parse business intel JSON (response=%s)", repr((response or "")[:200]))
            return None
        return BusinessIntelReport(
            business_name=data.get("business_name", ""),
            business_type=data.get("business_type", ""),
            city=data.get("city", ""),
            phone=data.get("phone", ""),
            rating=data.get("rating"),
            reviews_count=int(data.get("reviews_count") or 0),
            review_highlights=list(data.get("review_highlights") or []),
            unique_selling_points=list(data.get("unique_selling_points") or []),
            opening_hours_summary=data.get("opening_hours_summary", ""),
            target_audience=data.get("target_audience", ""),
            address=data.get("address", ""),
            website=data.get("website", ""),
        )

    # ── Stage 2: GPT-4o — Brand Strategist & Hebrew Copywriter ───────────────

    def _stage2_copywrite(self, intel: BusinessIntelReport) -> MarketingCopyBundle | None:
        from app.services.llm.router_service import LLMRouterService
        logger.info("[Stage 2] GPT-4o Brand Strategist — writing Hebrew copy")

        intel_json = json.dumps({
            "business_name": intel.business_name,
            "business_type": intel.business_type,
            "city": intel.city,
            "phone": intel.phone,
            "rating": intel.rating,
            "reviews_count": intel.reviews_count,
            "review_highlights": intel.review_highlights,
            "unique_selling_points": intel.unique_selling_points,
            "opening_hours_summary": intel.opening_hours_summary,
            "target_audience": intel.target_audience,
        }, ensure_ascii=False)

        response = LLMRouterService().call(
            "generate_site_copy",
            f"תובנות עסקיות:\n{intel_json}",
            system=_STAGE2_SYSTEM,
            model="gpt-4o",
            max_tokens=1000,
            json_mode=True,
        )
        data = _parse_json(response or "")
        if not data:
            logger.warning("[Stage 2] Could not parse GPT-4o JSON")
            return None
        return MarketingCopyBundle(
            business_name=data.get("business_name") or intel.business_name,
            hero_headline=data.get("hero_headline", ""),
            hero_subheadline=data.get("hero_subheadline", ""),
            about_us=data.get("about_us", ""),
            services=list(data.get("services") or []),
            contact_phone=data.get("contact_phone") or intel.phone,
            call_to_action=data.get("call_to_action", "צור קשר עכשיו"),
            tagline=data.get("tagline", ""),
            brand_personality=data.get("brand_personality", ""),
            color_scheme=data.get("color_scheme", "blue"),
        )

    # ── Stage 3: Claude — Senior Frontend Developer ───────────────────────────

    def _stage3_build_html(self, copy: MarketingCopyBundle) -> str | None:
        from app.services.llm.router_service import LLMRouterService
        logger.info("[Stage 3] Claude Frontend Developer — generating Tailwind HTML")

        tokens = _COLOR_TOKENS.get(copy.color_scheme, _COLOR_TOKENS["blue"])
        phone_clean = _clean_phone(copy.contact_phone)
        wa_url = f"https://wa.me/{phone_clean}" if phone_clean else "#"

        services_bullets = "\n".join(f"- {s}" for s in copy.services)

        design_brief = (
            f"Color palette: {copy.color_scheme} | "
            f"Gradient: from-{tokens['grad_from']} to-{tokens['grad_to']} | "
            f"Brand personality: {copy.brand_personality} | "
            f"Primary button class: {tokens['btn']}"
        )

        prompt = f"""צור דף HTML מלא עם הנתונים הבאים:

--- תוכן שיווקי ---
שם עסק: {copy.business_name}
כותרת ראשית: {copy.hero_headline}
תת-כותרת: {copy.hero_subheadline}
סלוגן: {copy.tagline}
אודות: {copy.about_us}
שירותים:
{services_bullets}
טלפון: {copy.contact_phone}
CTA: {copy.call_to_action}

--- הנחיות עיצוב ---
{design_brief}
WhatsApp: {wa_url}

דרישות:
- Hero section עם גרדיאנט וטקסט לבן, emoji מתאים לסוג העסק
- Services section עם grid של cards
- About section עם רקע בהיר
- Contact section עם כפתורי CTAs גדולים (טלפון + WhatsApp)
- Footer עם שם העסק
- כפתור WhatsApp צף בפינה שמאלית תחתונה (position: fixed)
- גופן Heebo דרך Google Fonts"""

        response = LLMRouterService().call(
            "build_site_html",
            prompt,
            system=_STAGE3_SYSTEM,
            model="claude-3-5-sonnet-20241022",
            max_tokens=6000,
        )
        if not response:
            return None
        # Ensure we have clean HTML
        html = response.strip()
        if not html.lower().startswith("<!doctype") and not html.lower().startswith("<html"):
            # Extract HTML block if Claude wrapped it
            m = re.search(r"<!DOCTYPE.*</html>", html, re.DOTALL | re.IGNORECASE)
            if m:
                html = m.group()
        return html
