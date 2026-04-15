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
    _design: "DesignConfig | None" = None  # stored for variant 2 reuse


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

REVIEWS POLICY:
- ONLY include reviews with 4 or 5 stars. Completely discard 1–3 star reviews.
- NEVER include complaints, criticisms, or negative experiences.
- If fewer than 2 positive reviews exist, generate 2 realistic 5-star placeholder reviews.

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
      "review_text": "<Short POSITIVE snippet in Hebrew — 4+ stars only>",
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
You are a world-class elite Frontend UI/UX Developer and conversion specialist.
Generate a high-converting, fully responsive, information-rich Hebrew landing page based on the provided JSON.

CRITICAL TECHNICAL CONSTRAINTS:
1. Output ONLY raw valid HTML. No explanations, no markdown wrappers.
2. The very first characters MUST be <!DOCTYPE html> and the very last MUST be </html>.

DESIGN & ARCHITECTURE RULES:
1. Use HTML5 and Tailwind CSS via CDN (<script src="https://cdn.tailwindcss.com"></script>).
2. The page MUST be strictly RTL with dir="rtl" on the <html> tag (Hebrew content).
3. Import Google Font 'Heebo' for Hebrew typography.
4. PAGE SECTIONS ORDER:
   Hero → Trust Badges → Services Grid → Reviews Carousel → Why-Us Bullets
   → Media Gallery (if media_urls present) → FAQ Section → About → SiteNest Badge
   → Contact CTA Strip → Footer
5. REVIEWS CAROUSEL: CSS-only auto-scrolling horizontal carousel. Each card includes:
   - Star rating (★ icons in gold), reviewer name, review quote text.
   - White background, soft shadow (shadow-lg), rounded-2xl, padding.
   - ONLY show reviews from top_reviews array that appear positive and constructive.
   - NEVER display complaints, low-star ratings, or negative content.
   - If top_reviews is empty, show 2 generic 5-star placeholder testimonials.
6. Show a Google rating badge above the carousel (e.g. "⭐ 4.8 / 5 — 120 ביקורות") ONLY if rating > 0.
7. UI Elements: soft gradients, subtle shadows, rounded corners, mobile-first responsive.
8. Floating sticky WhatsApp button at bottom-left corner (green circle, WA icon).
9. Apply design.json colors precisely — primary_color_hex as the dominant brand color.
10. Hero section: large gradient background, prominent headline, sub-headline, two CTA buttons (call + WhatsApp).
11. Add CSS scroll-reveal animations (IntersectionObserver or CSS @keyframes) and hover effects for cards and buttons.
12. Trust Badges section: 4 icon chips — "מענה מהיר", "אמינות מלאה", "מחיר הוגן", "ניסיון רב שנים".
13. Services section: minimum 6 rich cards with relevant emoji icons, benefit-driven descriptions (not just labels).
14. Why-Us section: 3–4 bullet points with large check icons on colored background strip.
15. Contact strip: highly actionable — click-to-call (tel: link), WhatsApp deep-link, and map/address if available.

MEDIA GALLERY (rule 16):
16. PHOTO/VIDEO GALLERY: if media_urls array is non-empty, render a "מהרשת החברתית שלנו" section
    BEFORE the FAQ section. Display up to 6 images/thumbnails in a responsive 3-column grid
    (2-col mobile). Each image: rounded-xl, object-cover, aspect-square, with subtle hover zoom.
    Link each image to the corresponding instagram_url or tiktok_url. If media_urls is empty → skip section entirely.

SOCIAL ASSETS (rule 17):
17. SOCIAL BAR in Footer: if any of facebook_url / instagram_url / tiktok_url is present,
    add a "עקבו אחרינו" row with SVG inline icons (Facebook blue, Instagram gradient, TikTok black).
    All links MUST have target="_blank" rel="noopener noreferrer".

TIKTOK / INSTAGRAM LINKS (rule 18):
18. If tiktok_url is present, add a "הסרטונים שלנו 🎬" section BEFORE the footer
    with a stylish pill CTA button linking to tiktok_url (black background, white text, TikTok logo).

OPENING HOURS (rule 19):
19. If easy_hours array is non-empty, render a "שעות פעילות" table inside the Contact section.

FAQ SECTION (rule 20):
20. FAQ: generate 4–5 realistic FAQ questions relevant to the business category.
    Use an accordion (HTML <details>/<summary>) with smooth open/close CSS transition.
    Style: clean white cards, bold question, muted answer text.
    Example questions: pricing, service area, response time, booking process, experience.

SITENEST RECOMMENDATION BADGE (rule 21):
21. Add a "SiteNest מאמתת עסק זה ✅" badge section just ABOVE the contact strip.
    Style: centered pill badge, primary color background, white text, checkmark icon.
    Text: "העסק הזה אומת ונבדק על-ידי SiteNest — הפלטפורמה המובילה לאתרי עסקים בישראל"
    Sub-text (smaller, muted): "האתר נבנה בטכנולוגיה מתקדמת ומותאם לחיפוש Google"

TRANSFORMATION LINE (rule 22):
22. Always add this tagline above the footer copyright line:
    "לקחנו את הידע המקצועי שלכם והפכנו אותו לחוויה מודרנית ומהירה ✨"
    Style it small, muted text.

INDUSTRY-SPECIFIC SECTIONS (rule 23):
23. Based on industry_type, add ONE extra unique section:
    - Restaurant/Cafe/Bar → "התפריט שלנו" section with 3-4 styled menu item cards (name + description in Hebrew)
    - Plumber/Electrician/Contractor/HVAC → "לפני ואחרי" before-after section with two placeholder divs showing improvement story
    - Lawyer/Accountant/Consultant → "תחומי התמחות" section as a styled timeline or numbered list with icons
    - Beauty/Salon/Spa/Nails → "הטיפולים שלנו בספא" section with service packages grid
    - Doctor/Clinic/Physiotherapy/Vet → "איך עובד הטיפול" 3-step process section
    - Gym/Yoga/Pilates/Fitness → "לוח זמנים שבועי" styled timetable section
    - If none match → "הישגים ומספרים" stats counter bar with 4 animated counters

CREDIBILITY STATS BAR (rule 24):
24. Add a "הספרות מדברות" horizontal stats bar between the Hero and Trust Badges sections.
    Show 3-4 impressive credibility numbers derived from the data (years of experience, number of clients,
    average rating, number of reviews, or area of service).
    Style: dark strip, large bold numbers in white, small label below, slight gradient.
    Animate the numbers counting up on scroll (IntersectionObserver + CSS counter animation).
    Example: "12+ שנות ניסיון" | "⭐ 4.8 דירוג ממוצע" | "200+ לקוחות מרוצים" | "כל הארץ"

UNIQUE DESIGN FINGERPRINT (rule 25):
25. Do NOT use the default Tailwind blue. Use the EXACT primary_color_hex and secondary_color_hex provided.
    Add ONE unique visual effect that matches the industry:
    - Food businesses: subtle floating food emoji animations in the hero
    - Beauty: soft shimmer/shine gradient on the hero
    - Technical trades: diagonal stripe pattern on section dividers
    - Professional services: geometric dots pattern on the hero background
    - Fitness: energy wave animation on the CTA button"""


# ── V2 System Prompt (Variant 2 — Premium Story) ─────────────────────────────

_CLAUDE_BUILDER_SYSTEM_V2 = """\
You are a world-class Frontend UI/UX Developer specializing in PREMIUM storytelling-driven digital experiences.
Generate a SECOND VARIANT of the Hebrew landing page — this variant uses a COMPLETELY DIFFERENT visual
and structural strategy from a first version. Make it feel like a different agency designed it.

VARIANT 2 — "Premium Story" Strategy:
- DARK IMMERSIVE HERO: Use a deep, rich hero background (dark overlay on gradient using primary_color_hex).
  Large centered text, soft glow effect, animated pulsing CTA button.
- NARRATIVE-FIRST FLOW: Lead with the business identity and story BEFORE listing services.
- ACHIEVEMENT COUNTER BAR: Full-width dark strip with 4 animated counters (years, clients, rating, area).
  Numbers count up on scroll using IntersectionObserver.
- ABOUT STORY SECTION: A magazine-style split layout — large quote on the left, text content on the right.
  Include a "מה מניע אותנו" (what drives us) personal paragraph from the about_us field.
- SERVICES as a stylish NUMBERED list (not a grid) — each item has a large accent number, bold title, description.
  Alternate background colors per item (light/accent/light) for visual rhythm.
- FEATURED TESTIMONIAL: One hero-sized testimonial block — large italic quote, big reviewer name,
  gold stars, soft gradient background. Then a grid of smaller review cards below.
- PROCESS STEPS: A "איך זה עובד" 3-step horizontal flow (icon → text → connector arrow) showing how to engage.
- FAQ as accordion (same as V1 but different styling — use card flip animation on open/close).
- FOOTER: Full dark footer with logo, tagline, all social links, and service area map mention.

PAGE SECTIONS ORDER (V2):
  Immersive Hero → Achievement Counter Bar → About Story → Services Numbered List →
  Featured Testimonial + Reviews Grid → Process Steps → Media Gallery (if present) →
  FAQ Accordion → SiteNest Badge → Contact CTA Strip → Dark Footer

CRITICAL TECHNICAL CONSTRAINTS:
1. Output ONLY raw valid HTML. No explanations, no markdown wrappers.
2. The very first characters MUST be <!DOCTYPE html> and the very last MUST be </html>.
3. Use HTML5 and Tailwind CSS via CDN (<script src="https://cdn.tailwindcss.com"></script>).
4. The page MUST be strictly RTL with dir="rtl" on the <html> tag (Hebrew content).
5. Import Google Font 'Heebo'.

DESIGN RULES (V2):
6. Use primary_color_hex as the hero background gradient (dark → primary color).
7. Secondary_color_hex for accent buttons, counter numbers, and featured highlights.
8. Dark sections (#1a1a2e or near-black) for counter bar and footer.
9. Cards: white background, premium shadow (shadow-2xl), rounded-3xl.
10. Typography: very large headings in the hero (text-6xl on desktop), smaller elsewhere.
11. Floating sticky WhatsApp button (same as V1).
12. Hero: large gradient background, prominent headline, sub-headline, two CTA buttons (call + WhatsApp).
13. ALL hover transitions: 300ms ease, scale 1.03 on cards.
14. Click-to-call and WhatsApp deep-link in contact section.
15. Google rating badge if rating > 0.
16. PHOTO/VIDEO GALLERY: if media_urls non-empty, render as full-width 3-column masonry grid.
    Each image: rounded-2xl, aspect-video (not square), subtle hover zoom.
17. SOCIAL BAR in footer: Facebook/Instagram/TikTok SVG icons, target="_blank".
18. TikTok section if tiktok_url present.
19. Opening hours table if easy_hours non-empty.
20. SiteNest verification badge above contact strip.
21. Tagline above footer: "לקחנו את הידע המקצועי שלכם והפכנו אותו לחוויה מודרנית ומהירה ✨"
22. INDUSTRY-SPECIFIC SECTION (same rule as V1 rule 23): add one extra section based on industry_type.
23. Unique V2 design fingerprint: add a subtle animated SVG wave divider between major sections.
    Use wave-shaped section separators (SVG path) with primary color fill."""


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

    def run(self, raw_maps_data: str, *, enrichment: dict | None = None, regeneration_note: str | None = None, draft_site_id: int | None = None, business_id: int | None = None) -> PipelineResult | None:
        logger.info("[Pipeline] Starting 5-stage AutoSite generation")
        enrichment = enrichment or {}
        self._track_draft_site_id = draft_site_id
        self._track_business_id = business_id
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

            result = PipelineResult(
                html=html,
                outreach_message=content.whatsapp_outreach_message or None,
                content=content,
            )
            result._design = design  # store for variant 2 reuse
            return result

        except Exception:
            logger.exception("[Pipeline] Unhandled top-level error")
            return None

    def generate_variant2(self, base_result: "PipelineResult", enrichment: dict) -> str | None:
        """Generate a second HTML variant from an already-run pipeline result.
        Reuses the content + design from base_result — only re-runs Stage 2 with V2 prompt.
        Returns raw HTML or None on failure.
        """
        if not base_result or not base_result.content:
            return None
        try:
            # Use same design if available, or create a default
            design = DesignConfig()
            if base_result.content:
                # Try to re-derive design from content (or use whatever was stored)
                design = getattr(base_result, '_design', DesignConfig())
            html = self._stage2_build(base_result.content, design, enrichment, variant=2)
            if html:
                logger.info("[Pipeline] Variant 2 generated — %d bytes", len(html))
            return html
        except Exception:
            logger.exception("[Pipeline] Variant 2 generation failed")
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
                "instagram_media_urls": profile.instagram_media_urls,
                "tiktok_media_urls": profile.tiktok_media_urls,
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
            response = LLMRouterService().call_tracked(
                "generate_site_copy",
                user_msg,
                system=_CONTENT_AGENT_SYSTEM,
                max_tokens=1200,
                json_mode=True,
                draft_site_id=getattr(self, '_track_draft_site_id', None),
                business_id=getattr(self, '_track_business_id', None),
                stage="stage1a_content",
            )
            data = _parse_json(response or "")
            if not data:
                logger.warning("[Stage 1a] No parseable JSON (response=%r)", (response or "")[:200])
                return None

            # parse top_reviews safely — filter out negative reviews (< 4 stars)
            raw_reviews = data.get("top_reviews") or []
            top_reviews: list[dict] = []
            if isinstance(raw_reviews, list):
                for r in raw_reviews:
                    if isinstance(r, dict):
                        stars = int(r.get("stars", 5))
                        if stars >= 4:   # ← only positive reviews on demo sites
                            top_reviews.append({
                                "reviewer_name": r.get("reviewer_name", ""),
                                "review_text": r.get("review_text", ""),
                                "stars": stars,
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
            response = LLMRouterService().call_tracked(
                "analyze_business_data",
                f"Business description for design analysis:\n{raw}",
                system=_GEMINI_DESIGN_SYSTEM,
                model="gemini-2.5-flash",
                max_tokens=400,
                json_mode=True,
                draft_site_id=getattr(self, '_track_draft_site_id', None),
                business_id=getattr(self, '_track_business_id', None),
                stage="stage1b_design",
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
        enrichment: dict,        variant: int = 1,    ) -> str | None:
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

            # Collect all media URLs from Apify (Instagram + TikTok thumbnails)
            media_urls: list[str] = []
            media_urls.extend(social.get("instagram_media_urls", []))
            media_urls.extend(social.get("tiktok_media_urls", []))
            media_urls = media_urls[:6]  # cap at 6 images in gallery

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
                "media_urls": media_urls,             # ← Apify-fetched IG/TikTok images
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

            response = LLMRouterService().call_tracked(
                "build_site_html",
                prompt,
                system=_CLAUDE_BUILDER_SYSTEM_V2 if variant == 2 else _CLAUDE_BUILDER_SYSTEM,
                model="claude-sonnet-4-6",
                max_tokens=8000,
                draft_site_id=getattr(self, '_track_draft_site_id', None),
                business_id=getattr(self, '_track_business_id', None),
                stage="stage2_build_html",
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
