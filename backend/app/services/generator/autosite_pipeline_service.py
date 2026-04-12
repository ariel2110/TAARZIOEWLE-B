"""AutoSite Multi-Agent Generation Pipeline
==========================================
Five specialized AI agents work together to produce a ready-to-send
Hebrew landing page + personalized WhatsApp outreach message.

  Stage 0  │ SocialDiscoveryService                │ Web Intelligence
           │ Discover & validate social/digital     │
           │ assets: FB, IG, TikTok, Easy, legacy  │

  Stage 1a │ GPT-4o (primary) / Grok (fallback)   │ Content Manager
           │ Raw Maps text → content.json           │ (parallel)
           │ + personalized WhatsApp outreach msg   │

  Stage 1b │ Gemini 2.5 Flash                      │ Style Director
           │ Business profile → design.json         │ (parallel)

  Stage 2  │ Claude Sonnet 4-6                      │ Master Builder
           │ content.json + design.json + social   │
           │ → HTML with SocialBar + TikTok embed  │

  Stage 4  │ Python Backend (DraftSiteService)      │ Operations Manager
           │ Save HTML, assign URL, store outreach  │
"""
from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Typed data contracts ──────────────────────────────────────────────────────

@dataclass
class ContentBundle:
    """Output of Stage 1a (GPT-4o/Grok): full Hebrew copy + outreach message."""
    business_name: str = ""
    industry_type: str = ""          # e.g. "Electrician", "Restaurant" — English
    hero_headline: str = ""
    hero_subheadline: str = ""
    about_us: str = ""
    services: list[str] = field(default_factory=list)
    top_reviews: list[dict] = field(default_factory=list)  # [{reviewer_name, review_text, stars}]
    contact_phone: str = ""
    call_to_action: str = ""
    whatsapp_outreach_message: str = ""  # personalized message with [DEMO_LINK] placeholder


@dataclass
class DesignConfig:
    """Output of Stage 1b (Gemini): visual identity configuration."""
    theme_vibe: str = "Modern"
    primary_color_hex: str = "#1E3A8A"
    secondary_color_hex: str = "#3B82F6"
    background_style: str = "light"
    ui_instructions: str = "Use a clean professional design with modern typography."


@dataclass
class PipelineResult:
    """Full output returned by AutoSitePipelineService.run()"""
    html: str
    outreach_message: str | None = None   # ready to send (no [DEMO_LINK] yet)
    content: ContentBundle | None = None


# ── System Prompts ─────────────────────────────────────────────────────────────

_CONTENT_AGENT_SYSTEM = """\
You are an elite direct-response copywriter and a strict data processor.
Your objective is to analyze raw Google Maps data of a local Israeli business and output marketing copy for a landing page, along with a personalized outreach message.
The entire output MUST be in fluent, natural HEBREW, but the JSON keys must remain in English.

QUALITY BAR:
- The copy must feel premium, specific, and local (Israel-first tone).
- Avoid generic phrases; include concrete trust and outcome language.
- Services should describe customer outcomes, not only labels.
- Keep messaging conversion-focused: trust, clarity, urgency, and action.

CRITICAL RULES:
1. You are communicating with a machine. You MUST output strictly and exclusively in valid JSON format.
2. DO NOT include any conversational text, greetings, or explanations before or after the JSON.
3. ABSOLUTELY NO MARKDOWN. Do not wrap the output in ```json blocks. Start immediately with { and end with }.

REQUIRED JSON STRUCTURE:
{
  "business_name": "<Exact business name>",
  "industry_type": "<e.g., Restaurant, Plumber, Lawyer - IN ENGLISH>",
  "hero_headline": "<A powerful, catchy main headline in Hebrew designed to capture attention>",
  "hero_subheadline": "<A short, persuasive sub-headline in Hebrew explaining the value proposition>",
    "about_us": "<A compelling paragraph in Hebrew with credibility proof, differentiator, and concrete value>",
  "services": [
    "<Service 1 in Hebrew>",
    "<Service 2 in Hebrew>",
        "<Service 3 in Hebrew>",
        "<Service 4 in Hebrew>",
        "<Service 5 in Hebrew>",
        "<Service 6 in Hebrew>"
  ],
  "top_reviews": [
    {
      "reviewer_name": "<Name>",
      "review_text": "<Short positive snippet in Hebrew>",
      "stars": 5
    }
  ],
  "contact_phone": "<Extract phone number, leave empty if none>",
    "call_to_action": "<Strong and urgent action button text in Hebrew>",
  "whatsapp_outreach_message": "<Write a short (3-4 sentences), friendly, and highly persuasive WhatsApp message in Hebrew addressed to the business owner. Tell them you noticed they have great reviews but no website, and that you built them a free demo. Be direct, casual, and warm. Use placeholder [DEMO_LINK] for the URL.>"
}"""

_GEMINI_DESIGN_SYSTEM = """\
You are an expert Art Director and UI/UX Designer.
Analyze the provided local business description and output a JSON configuration detailing the visual identity for their website.

DESIGN QUALITY RULES:
- Choose a bold, non-generic visual direction aligned to the business category.
- Colors must have strong contrast and a clear conversion accent.
- The identity should feel modern, premium, and memorable.
- Prefer distinctive palettes over plain corporate defaults.

CRITICAL RULES:
1. Output strictly valid JSON only — no markdown, no explanations.

REQUIRED JSON STRUCTURE:
{
  "theme_vibe": "<One word: Modern/Rustic/Corporate/Playful/Elegant>",
  "primary_color_hex": "<Dominant brand color in HEX, e.g. #1E3A8A>",
  "secondary_color_hex": "<Complementary accent color in HEX>",
  "background_style": "<light or dark>",
  "ui_instructions_for_developer": "<1-2 sentences on exact aesthetic>"
}"""

_CLAUDE_BUILDER_SYSTEM = """\
You are a world-class elite Frontend UI/UX Developer.
Generate a high-converting, fully responsive Hebrew landing page based on the provided JSON.

CRITICAL TECHNICAL CONSTRAINTS:
1. Output ONLY raw valid HTML. No explanations, no markdown wrappers.
2. The very first characters MUST be <!DOCTYPE html> and the very last MUST be </html>.

DESIGN & ARCHITECTURE RULES:
1. Use HTML5 and Tailwind CSS via CDN (<script src="https://cdn.tailwindcss.com"></script>).
2. The page MUST be strictly RTL with dir="rtl" on the <html> tag (Hebrew content).
3. Import Google Font 'Heebo' for Hebrew typography.
4. PAGE SECTIONS ORDER: Hero → Trust badges → Services grid → Reviews Carousel → Why-us bullets → About → Contact CTA strip → Footer.
5. REVIEWS CAROUSEL: CSS-only auto-scrolling horizontal carousel. Each card includes:
   - Star rating (★ icons in gold), reviewer name, review quote text.
   - White background, soft shadow (shadow-lg), rounded-2xl, padding.
   - If top_reviews array is empty, show a single placeholder testimonial.
6. Show a Google rating badge above the carousel (e.g. "⭐ 4.8 / 5 — 120 ביקורות").
7. UI Elements: soft gradients, subtle shadows, rounded corners, mobile-first responsive.
8. Floating sticky WhatsApp button at bottom-left corner (green circle, WA icon).
9. Apply design.json colors precisely — primary_color_hex as the dominant brand color.
10. Hero section: large gradient background, prominent headline, CTA button.
11. Add subtle reveal animations and tasteful hover effects for cards and buttons.
12. Add trust chips such as fast response, reliability, and fair pricing.
13. Services section should render at least 6 rich cards with icons and benefit text.
14. Contact strip should be highly actionable: click-to-call, WhatsApp, and map link where available.

SOCIAL ASSETS (render ONLY when the URLs are non-empty strings):
15. SOCIAL BAR in Footer: if any of facebook_url / instagram_url / tiktok_url is present,
    add a "עקבו אחרינו" row with icon-links. Use SVG inline icons (Facebook blue, Instagram
    gradient, TikTok black). All links MUST have target="_blank" rel="noopener noreferrer".
    Example structure:
      <div class="flex gap-4 justify-center mt-4">
        <!-- Only include each icon if the URL is non-empty -->
        <a href="{facebook_url}" target="_blank" rel="noopener noreferrer" aria-label="Facebook"><!-- fb svg --></a>
        <a href="{instagram_url}" target="_blank" rel="noopener noreferrer" aria-label="Instagram"><!-- ig svg --></a>
        <a href="{tiktok_url}" target="_blank" rel="noopener noreferrer" aria-label="TikTok"><!-- tiktok svg --></a>
      </div>
16. TIKTOK EMBED: if tiktok_url is present, add a "הסרטונים שלנו" section BEFORE the footer
    with a centered TikTok profile link button (styled pill button linking to tiktok_url).
    Do NOT use <blockquote> embed — just a stylish CTA button to the TikTok page.
17. OPENING HOURS: if easy_hours array is non-empty, render a שעות פעילות table inside the
    Contact section listing each entry on its own row.
18. TRANSFORMATION LINE: always add the following tagline above the footer copyright line:
    "לקחנו את הידע המקצועי שלכם והפכנו אותו לחוויה מודרנית ומהירה ✨"
    Style it small, muted text."""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _clean_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("0") and len(digits) == 10:
        digits = "972" + digits[1:]
    return digits


def _parse_json(raw: str) -> dict | None:
    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


# ── Pipeline ──────────────────────────────────────────────────────────────────

class AutoSitePipelineService:
    """
    Orchestrates the 4-agent AutoSite pipeline.

    Usage:
        result = AutoSitePipelineService().run(raw_maps_data, enrichment={...})
        result.html              # full Tailwind HTML page
        result.outreach_message  # WhatsApp message with [DEMO_LINK] placeholder
        result.content           # ContentBundle with all structured data
    """

    def run(self, raw_maps_data: str, *, enrichment: dict | None = None, regeneration_note: str | None = None) -> PipelineResult | None:
        logger.info("[Pipeline] Starting 5-stage AutoSite generation")
        enrichment = enrichment or {}
        try:
            design: DesignConfig = DesignConfig()
            content: ContentBundle | None = None

            # ── Stage 0: Social & Web Intelligence Discovery ──────────────────
            social = self._stage0_social_discovery(enrichment)
            # Merge social profile into enrichment so Stage 2 (Claude) can use it
            enrichment = {**enrichment, "_social": social}

            # ── Stage 1: Parallel ─────────────────────────────────────────────
            # Stage 1a: GPT-4o (primary) / Grok (auto-fallback) → content + outreach
            # Stage 1b: Gemini → design config
            with ThreadPoolExecutor(max_workers=2) as pool:
                f_content = pool.submit(self._stage1a_content, raw_maps_data, regeneration_note, social)
                f_design = pool.submit(self._stage1b_design, raw_maps_data)

                content = f_content.result(timeout=90)
                try:
                    design = f_design.result(timeout=30)
                except Exception:
                    logger.info("[Stage 1b] Design timed-out / failed — using DesignConfig defaults")
                    design = DesignConfig()

            if not content:
                logger.warning("[Pipeline] Stage 1a failed — aborting")
                return None

            logger.info("[Pipeline] Stage 1a OK — business=%r industry=%s", content.business_name, content.industry_type)
            logger.info("[Pipeline] Stage 1b OK — vibe=%r color=%s", design.theme_vibe, design.primary_color_hex)

            # ── Stage 2: Claude → HTML ────────────────────────────────────────
            html = self._stage2_build(content, design, enrichment)
            if not html:
                logger.warning("[Pipeline] Stage 2 (Claude HTML) failed — aborting")
                return None

            logger.info("[Pipeline] Stage 2 OK — %d bytes", len(html))

            return PipelineResult(
                html=html,
                outreach_message=content.whatsapp_outreach_message or None,
                content=content,
            )

        except Exception:
            logger.exception("[Pipeline] Unhandled top-level error")
            return None

    # ── Stage 0: Social & Web Intelligence ───────────────────────────────────

    def _stage0_social_discovery(self, enrichment: dict) -> dict:
        """Run social/web discovery. Returns a plain dict for safe serialisation."""
        try:
            from app.services.enrichment.social_discovery_service import SocialDiscoveryService
            profile = SocialDiscoveryService().discover(
                business_name=enrichment.get("name", ""),
                city=enrichment.get("city", ""),
                phone=enrichment.get("phone", ""),
                website=enrichment.get("website_url", ""),
                category=enrichment.get("category", ""),
            )
            result = {
                "facebook_url": profile.facebook_url,
                "instagram_url": profile.instagram_url,
                "tiktok_url": profile.tiktok_url,
                "easy_url": profile.easy_url,
                "b144_url": profile.b144_url,
                "legacy_site_url": profile.legacy_site_url,
                "social_verified": profile.social_verified,
                "social_confidence": profile.social_confidence,
                "digital_gap_label": profile.digital_gap_label,
                "easy_hours": profile.easy_hours,
                "easy_services": profile.easy_services,
                "legacy_text_snippets": profile.legacy_text_snippets,
                "tone_hint": profile.tone_hint,
            }
            logger.info("[Stage 0] Social discovery complete — gap=%r confidence=%d",
                        profile.digital_gap_label, profile.social_confidence)
            return result
        except Exception:
            logger.exception("[Stage 0] Social discovery failed — proceeding without social data")
            return {}

    # ── Stage 1a: GPT-4o (primary) / Grok (auto-fallback via router) ─────────

    def _stage1a_content(self, raw: str, regeneration_note: str | None = None, social: dict | None = None) -> ContentBundle | None:
        try:
            from app.services.llm.router_service import LLMRouterService
            logger.info("[Stage 1a] GPT-4o Content Manager — generating copy + outreach JSON")
            # Build user message — inject note if this is a regeneration
            user_msg = f"Raw Google Maps Data:\n{raw}"
            if regeneration_note and regeneration_note.strip():
                user_msg += (
                    f"\n\n=== REGENERATION INSTRUCTIONS FROM OWNER ===\n"
                    f"{regeneration_note.strip()}\n"
                    "Apply these changes to the generated website copy. "
                    "Keep all unchanged sections; only modify what the instructions explicitly request."
                )
                logger.info("[Stage 1a] regeneration_note injected (%d chars)", len(regeneration_note))

            # Inject social tone & legacy text hints
            if social:
                tone = social.get("tone_hint", "")
                legacy_snippets = social.get("legacy_text_snippets", [])
                easy_services = social.get("easy_services", [])
                tone_map = {
                    "young_creative": "צעיר, יצירתי ודינמי — העסק פעיל בטיקטוק",
                    "visual_casual": "ויזואלי וקליל — בעל נוכחות חזקה באינסטגרם",
                    "formal_local": "מקצועי ומקומי — ממוקד דירוג גוגל ורישום ב-Easy",
                    "casual": "ידידותי וקרוב — עסק שמח בפייסבוק",
                }
                if tone and tone in tone_map:
                    user_msg += f"\n\n=== TONE OF VOICE ===\n{tone_map[tone]}\nהתאם את הכתיבה לסגנון זה."
                if legacy_snippets:
                    user_msg += f"\n\n=== PROFESSIONAL CONTENT FROM LEGACY SITE ===\n"
                    user_msg += "השתמש בקטעי הטקסט הבאים (מהאתר הישן של העסק) כמקור לתוכן מקצועי, שנות ניסיון, הסמכות וכו':\n"
                    user_msg += "\n".join(f'- {s}' for s in legacy_snippets)
                if easy_services:
                    user_msg += f"\n\n=== SERVICES FROM EASY DIRECTORY ===\nשירותים מאומתים מ-Easy:\n"
                    user_msg += "\n".join(f'- {s}' for s in easy_services)
            response = LLMRouterService().call(
                "generate_site_copy",
                user_msg,
                system=_CONTENT_AGENT_SYSTEM,
                max_tokens=1200,
                json_mode=True,
            )
            data = _parse_json(response or "")
            if not data:
                logger.warning("[Stage 1a] No parseable JSON (response=%r)", (response or "")[:200])
                return None

            # parse top_reviews safely
            raw_reviews = data.get("top_reviews") or []
            top_reviews: list[dict] = []
            if isinstance(raw_reviews, list):
                for r in raw_reviews:
                    if isinstance(r, dict):
                        top_reviews.append({
                            "reviewer_name": r.get("reviewer_name", ""),
                            "review_text": r.get("review_text", ""),
                            "stars": int(r.get("stars", 5)),
                        })

            return ContentBundle(
                business_name=data.get("business_name", ""),
                industry_type=data.get("industry_type", ""),
                hero_headline=data.get("hero_headline", ""),
                hero_subheadline=data.get("hero_subheadline", ""),
                about_us=data.get("about_us", ""),
                services=list(data.get("services") or []),
                top_reviews=top_reviews,
                contact_phone=data.get("contact_phone", ""),
                call_to_action=data.get("call_to_action", "צור קשר עכשיו"),
                whatsapp_outreach_message=data.get("whatsapp_outreach_message", ""),
            )
        except Exception:
            logger.exception("[Stage 1a] Unhandled error")
            return None

    # ── Stage 1b: Gemini → design config ─────────────────────────────────────

    def _stage1b_design(self, raw: str) -> DesignConfig:
        """Always returns a DesignConfig — never raises."""
        try:
            from app.services.llm.router_service import LLMRouterService
            logger.info("[Stage 1b] Gemini Style Director — generating design JSON")
            response = LLMRouterService().call(
                "analyze_business_data",
                f"Business description for design analysis:\n{raw}",
                system=_GEMINI_DESIGN_SYSTEM,
                model="gemini-2.5-flash",
                max_tokens=400,
                json_mode=True,
            )
            data = _parse_json(response or "")
            if data:
                return DesignConfig(
                    theme_vibe=data.get("theme_vibe", "Modern"),
                    primary_color_hex=data.get("primary_color_hex", "#1E3A8A"),
                    secondary_color_hex=data.get("secondary_color_hex", "#3B82F6"),
                    background_style=data.get("background_style", "light"),
                    ui_instructions=data.get("ui_instructions_for_developer", ""),
                )
            logger.info("[Stage 1b] Unparseable design response — using defaults")
        except Exception:
            logger.info("[Stage 1b] Design agent failed (quota?) — using defaults")
        return DesignConfig()

    # ── Stage 2: Claude → Master Builder ─────────────────────────────────────

    def _stage2_build(
        self,
        content: ContentBundle,
        design: DesignConfig,
        enrichment: dict,
    ) -> str | None:
        try:
            from app.services.llm.router_service import LLMRouterService
            logger.info("[Stage 2] Claude Master Builder — generating Tailwind HTML")

            phone_clean = _clean_phone(content.contact_phone)
            wa_url = f"https://wa.me/{phone_clean}" if phone_clean else "#"
            tel_url = f"tel:{phone_clean}" if phone_clean else "#"

            # Merge AI-generated reviews with enrichment reviews
            reviews_for_claude: list[dict] = list(content.top_reviews)
            if not reviews_for_claude:
                # fallback: wrap enrichment top_review in same format
                top_review_text = enrichment.get("top_review") or ""
                if top_review_text:
                    reviews_for_claude = [{"reviewer_name": "לקוח מרוצה", "review_text": top_review_text, "stars": 5}]

            rating = enrichment.get("rating")
            reviews_count = enrichment.get("reviews_count") or 0
            opening_hours: list[str] = enrichment.get("opening_hours") or []
            if isinstance(opening_hours, str):
                opening_hours = [opening_hours]
            social: dict = enrichment.get("_social") or {}

            content_json = json.dumps({
                "business_name": content.business_name,
                "industry_type": content.industry_type,
                "hero_headline": content.hero_headline,
                "hero_subheadline": content.hero_subheadline,
                "about_us": content.about_us,
                "services": content.services,
                "top_reviews": reviews_for_claude[:8],
                "contact_phone": content.contact_phone,
                "call_to_action": content.call_to_action,
                "whatsapp_url": wa_url,
                "tel_url": tel_url,
                "rating": rating,
                "reviews_count": reviews_count,
                "opening_hours": opening_hours[:7],
                # ── Social & digital assets (from Stage 0) ──────────────────
                "social": {
                    "facebook_url": social.get("facebook_url", ""),
                    "instagram_url": social.get("instagram_url", ""),
                    "tiktok_url": social.get("tiktok_url", ""),
                    "easy_url": social.get("easy_url", ""),
                    "legacy_site_url": social.get("legacy_site_url", ""),
                    "social_verified": social.get("social_verified", False),
                    "easy_hours": social.get("easy_hours", []),
                    "digital_gap_label": social.get("digital_gap_label", ""),
                } if social else {},
            }, ensure_ascii=False, indent=2)

            design_json = json.dumps({
                "theme_vibe": design.theme_vibe,
                "primary_color_hex": design.primary_color_hex,
                "secondary_color_hex": design.secondary_color_hex,
                "background_style": design.background_style,
                "ui_instructions_for_developer": design.ui_instructions,
            }, ensure_ascii=False, indent=2)

            prompt = (
                "Please build the complete site.\n\n"
                f"CONTENT JSON:\n{content_json}\n\n"
                f"DESIGN INSTRUCTIONS JSON:\n{design_json}"
            )

            response = LLMRouterService().call(
                "build_site_html",
                prompt,
                system=_CLAUDE_BUILDER_SYSTEM,
                model="claude-sonnet-4-6",
                max_tokens=8000,
            )
            if not response:
                return None
            html = response.strip()
            if not html.lower().startswith("<!doctype") and not html.lower().startswith("<html"):
                m = re.search(r"<!DOCTYPE.*</html>", html, re.DOTALL | re.IGNORECASE)
                if m:
                    html = m.group()
            if html and not html.lower().rstrip().endswith("</html>"):
                html = html.rstrip() + "\n</html>"
            return html
        except Exception:
            logger.exception("[Stage 2] Unhandled error")
            return None
