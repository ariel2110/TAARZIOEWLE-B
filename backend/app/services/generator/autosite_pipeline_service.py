"""AutoSite Multi-Agent Generation Pipeline
==========================================
Three specialized AI agents work in an optimized flow to produce a
beautiful, conversion-focused Hebrew landing page for a local business.

  Stage 1a | GPT-4o            | Content Manager & Hebrew Copywriter (parallel)
  Stage 1b | Gemini 2.0 Flash  | Style & Design Director             (parallel)
  Stage 2  | Claude 3.5 Sonnet | Master Builder  (content + design -> full HTML)
"""
from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Typed data contracts between agents ──────────────────────────────────────

@dataclass
class ContentBundle:
    """Output of Stage 1a (GPT-4o): complete Hebrew marketing copy."""
    business_name: str = ""
    hero_headline: str = ""
    hero_subheadline: str = ""
    about_us: str = ""
    services: list[str] = field(default_factory=list)
    contact_phone: str = ""
    call_to_action: str = ""


@dataclass
class DesignConfig:
    """Output of Stage 1b (Gemini): visual identity configuration."""
    theme_vibe: str = "Modern"
    primary_color_hex: str = "#1E3A8A"
    secondary_color_hex: str = "#3B82F6"
    background_style: str = "light"
    ui_instructions: str = "Use a clean professional design with modern typography."


# ── System Prompts ─────────────────────────────────────────────────────────────

_GPT4O_CONTENT_SYSTEM = (
    "You are an elite direct-response copywriter and a strict data structurer.\n"
    "Your objective is to analyze raw Google Maps data of a local Israeli business and write "
    "high-converting, persuasive marketing copy for a single-page landing page.\n"
    "The entire output MUST be in fluent, natural HEBREW, but the JSON keys must remain in English.\n\n"
    "CRITICAL RULES:\n"
    "1. You MUST output strictly and exclusively in valid JSON format.\n"
    "2. DO NOT include any conversational text before or after the JSON.\n"
    "3. DO NOT wrap the output in markdown blocks like ```json. Just return the raw JSON object.\n\n"
    'REQUIRED JSON STRUCTURE:\n'
    '{\n'
    '  "business_name": "<Exact business name>",\n'
    '  "hero_headline": "<A powerful, catchy main headline in Hebrew>",\n'
    '  "hero_subheadline": "<A short, persuasive sub-headline in Hebrew>",\n'
    '  "about_us": "<A compelling paragraph in Hebrew highlighting their strengths>",\n'
    '  "services": ["<Service 1>", "<Service 2>", "<Service 3>"],\n'
    '  "contact_phone": "<Extract phone number, leave empty if none>",\n'
    '  "call_to_action": "<Strong action button text in Hebrew>"\n'
    '}'
)

_GEMINI_DESIGN_SYSTEM = (
    "You are an expert Art Director and UI/UX Designer.\n"
    "Analyze the provided local business description and output a JSON configuration "
    "detailing the visual identity for their website.\n\n"
    "CRITICAL RULES:\n"
    "1. Output strictly valid JSON only — no markdown, no explanations.\n\n"
    'REQUIRED JSON STRUCTURE:\n'
    '{\n'
    '  "theme_vibe": "<One word: Modern/Rustic/Corporate/Playful/Elegant>",\n'
    '  "primary_color_hex": "<Dominant brand color in HEX, e.g. #1E3A8A>",\n'
    '  "secondary_color_hex": "<Complementary accent color in HEX>",\n'
    '  "background_style": "<light or dark>",\n'
    '  "ui_instructions_for_developer": "<1-2 sentences on exact aesthetic>"\n'
    '}'
)

_CLAUDE_BUILDER_SYSTEM = (
    "You are a world-class elite Frontend UI/UX Developer.\n"
    "Generate a high-converting, fully responsive Hebrew landing page based on the provided JSON.\n\n"
    "CRITICAL TECHNICAL CONSTRAINTS:\n"
    "1. Output ONLY raw valid HTML. No explanations, no markdown wrappers.\n"
    "2. The very first characters MUST be <!DOCTYPE html> and the very last MUST be </html>.\n\n"
    "DESIGN & ARCHITECTURE RULES:\n"
    "1. Use HTML5 and Tailwind CSS via CDN (<script src=\"https://cdn.tailwindcss.com\"></script>).\n"
    "2. The page MUST be strictly RTL with dir=\"rtl\" on the <html> tag.\n"
    "3. Import Google Font 'Heebo' for Hebrew typography.\n"
    "4. PAGE SECTIONS ORDER: Hero -> Services -> Reviews Carousel -> About -> Contact -> Footer.\n"
    "5. REVIEWS CAROUSEL: CSS-only auto-scrolling. Each card: star rating, quote text, avatar placeholder.\n"
    "6. UI Elements: soft gradients, subtle shadows, rounded corners, mobile-first responsive.\n"
    "7. Floating sticky WhatsApp button at bottom-left corner.\n"
    "8. Apply design.json colors precisely — primary_color_hex as the dominant brand color."
)


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
    """Orchestrates the multi-agent AutoSite pipeline.

    html = AutoSitePipelineService().run(
        raw_maps_data,
        enrichment={
            'top_review': '...',
            'reviews': ['...'],
            'rating': 4.8,
            'reviews_count': 120,
            'opening_hours': [...],
        }
    )
    Returns full HTML string, or None on failure.
    """

    def run(self, raw_maps_data: str, *, enrichment: dict | None = None) -> str | None:
        logger.info("[Pipeline] Starting parallel AutoSite generation")
        enrichment = enrichment or {}
        try:
            design: DesignConfig = DesignConfig()  # pre-set safe fallback
            content: ContentBundle | None = None

            with ThreadPoolExecutor(max_workers=2) as pool:
                f_content = pool.submit(self._stage1a_content, raw_maps_data)
                f_design = pool.submit(self._stage1b_design, raw_maps_data)

                content = f_content.result(timeout=90)
                try:
                    design = f_design.result(timeout=30)
                except Exception:
                    logger.info("[Stage 1b] Design future timed-out or raised, using DesignConfig defaults")
                    design = DesignConfig()

            if not content:
                logger.warning("[Pipeline] Stage 1a (content) failed — aborting")
                return None

            logger.info("[Pipeline] Stage 1a OK headline=%r", (content.hero_headline or "")[:50])
            logger.info("[Pipeline] Stage 1b design.vibe=%r", design.theme_vibe)

            html = self._stage2_build(content, design, enrichment)
            if not html:
                logger.warning("[Pipeline] Stage 2 (Claude HTML) failed — aborting")
                return None

            logger.info("[Pipeline] Stage 2 OK, HTML %d bytes", len(html))
            return html

        except Exception:
            logger.exception("[Pipeline] Unhandled top-level error")
            return None

    # ── Stage 1a: GPT-4o ─────────────────────────────────────────────────────

    def _stage1a_content(self, raw: str) -> ContentBundle | None:
        try:
            from app.services.llm.router_service import LLMRouterService
            logger.info("[Stage 1a] GPT-4o Content Manager — generating copy JSON")
            response = LLMRouterService().call(
                "generate_site_copy",
                f"Raw Google Maps Data:\n{raw}",
                system=_GPT4O_CONTENT_SYSTEM,
                model="grok-3-mini",
                max_tokens=900,
                json_mode=True,
            )
            data = _parse_json(response or "")
            if not data:
                logger.warning("[Stage 1a] No parseable JSON from GPT-4o (response=%r)", (response or "")[:200])
                return None
            return ContentBundle(
                business_name=data.get("business_name", ""),
                hero_headline=data.get("hero_headline", ""),
                hero_subheadline=data.get("hero_subheadline", ""),
                about_us=data.get("about_us", ""),
                services=list(data.get("services") or []),
                contact_phone=data.get("contact_phone", ""),
                call_to_action=data.get("call_to_action", "צור קשר עכשיו"),
            )
        except Exception:
            logger.exception("[Stage 1a] Unhandled error")
            return None

    # ── Stage 1b: Gemini ─────────────────────────────────────────────────────

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
            logger.info("[Stage 1b] Design response unparseable, using defaults")
        except Exception:
            logger.info("[Stage 1b] Design agent failed (Gemini quota?), using defaults")
        return DesignConfig()

    # ── Stage 2: Claude ───────────────────────────────────────────────────────

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

            reviews_raw: list[str] = []
            enrichment_reviews = enrichment.get("reviews") or []
            if isinstance(enrichment_reviews, list):
                reviews_raw = [r for r in enrichment_reviews if isinstance(r, str) and len(r) > 20]
            if not reviews_raw and enrichment.get("top_review"):
                reviews_raw = [enrichment["top_review"]]

            rating = enrichment.get("rating")
            reviews_count = enrichment.get("reviews_count") or 0
            opening_hours: list[str] = enrichment.get("opening_hours") or []
            if isinstance(opening_hours, str):
                opening_hours = [opening_hours]

            content_json = json.dumps({
                "business_name": content.business_name,
                "hero_headline": content.hero_headline,
                "hero_subheadline": content.hero_subheadline,
                "about_us": content.about_us,
                "services": content.services,
                "contact_phone": content.contact_phone,
                "call_to_action": content.call_to_action,
                "whatsapp_url": wa_url,
                "tel_url": tel_url,
                "rating": rating,
                "reviews_count": reviews_count,
                "reviews": reviews_raw[:10],
                "opening_hours": opening_hours[:7],
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
                f"Use this verified content:\n{content_json}\n\n"
                f"Strictly follow these design guidelines:\n{design_json}\n\n"
                "REVIEWS CAROUSEL RULES:\n"
                "- Build a horizontal auto-scrolling carousel (CSS animation, no JS library).\n"
                "- Each card: white background, soft shadow, rounded-2xl, star rating, review quote text.\n"
                "- If only one review is in the JSON, display it as a single featured testimonial.\n"
                f"- Show Google rating badge: {rating or 'N/A'} / 5 — {reviews_count} ביקורות\n"
                "- Carousel section background: subtle gray or secondary color at very low opacity."
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
            # Ensure proper HTML closure
            if html and not html.lower().rstrip().endswith("</html>"):
                html = html.rstrip() + "\n</html>"
            return html
        except Exception:
            logger.exception("[Stage 2] Unhandled error")
            return None
