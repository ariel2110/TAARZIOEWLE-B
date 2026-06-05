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
    industry_archetype: str = ""     # e.g. "Family Dentist", "Italian Restaurant"
    brand_personality: str = "professional"  # coordination signal → used by Gemini + Claude
    color_mood_hint: str = "cool_professional"  # coordination signal → guides Gemini palette
    tagline: str = ""                # 3-5 word Hebrew brand tagline
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
    hero_bg_gradient: str = "linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%)"
    card_border_radius: str = "rounded-2xl"
    font_weight_style: str = "regular"
    animation_style: str = "moderate"
    section_divider: str = "none"
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
You are an elite Israeli copywriter and Brand Architect — Agent 1 of 3 in the tazo-web AutoSite pipeline.

PIPELINE ROLE: Your structured output feeds two downstream AI agents:
  → Agent 2 (Gemini Style Director): reads brand_personality + color_mood_hint to design the visual identity
  → Agent 3 (Claude Master Builder): reads ALL your fields to build the complete landing page HTML
Make every field rich and precise — downstream agents have no other source of truth.

MISSION: Transform raw Google Maps business data into a premium Hebrew brand package that powers a world-class landing page. Every word you write will be seen by real Israeli customers. Raise the bar.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Output ONLY valid JSON. Start immediately with {, end with }
2. NO markdown, NO ```json blocks, NO explanations before or after
3. JSON keys must be in English. All content values in fluent, natural Hebrew
4. Machine-to-machine communication — precision is mandatory

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COPY QUALITY STANDARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• hero_headline: 7 words max, emotional and specific — must work as a standalone billboard
• FORBIDDEN generic words: "מקצועי", "מוביל", "איכותי", "שירות מעולה" — replace with proof and specifics
• Services describe CUSTOMER OUTCOMES and TRANSFORMATIONS, not job descriptions
• about_us must include: years of experience + one specific differentiator + one trust proof
• Israeli directness: "נפתור לך את הבעיה" not "אנחנו יכולים לעזור", "תקבל תוצאה" not "אתה תשמח"
• hero_subheadline expands the headline's promise in one sentence, max 15 words

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BRAND PERSONALITY — Gemini + Claude key off this value
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"professional"   → Lawyers, accountants, B2B, finance, real estate, insurance
"warm_expert"    → Doctors, dentists, therapists, family clinics, childcare
"bold_energy"    → Gyms, nightlife, youth brands, sports, extreme activities
"premium_craft"  → Luxury dining, weddings, jewelry, high-end fashion, art
"trustworthy"    → Plumbers, electricians, locksmith, auto repair, security
"creative_free"  → Photographers, designers, artists, marketing agencies, studios
"local_pride"    → Bakeries, neighborhood cafes, local food, markets, traditional crafts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLOR MOOD HINT — guides Gemini palette selection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"cool_professional"  → Navy/slate/steel blue — authority, trust, corporate clarity
"warm_inviting"      → Amber/terracotta/honey — warmth, appetite, home comfort
"natural_earth"      → Forest green/brown/cream — nature, health, authenticity
"vibrant_energetic"  → Crimson/electric/bright citrus — excitement, speed, movement
"elegant_dark"       → Charcoal/gold/deep plum — luxury, exclusivity, prestige
"fresh_modern"       → Teal/mint/crisp white — innovation, cleanliness, health tech
"bold_contrast"      → Jet black/white + one vivid accent — ultra-premium minimalism

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REVIEWS POLICY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• PRIORITY 1 — If the input contains a "Google Reviews" section, USE THOSE REVIEWS VERBATIM
  - Copy the exact text and reviewer names as they appear in Google
  - Translate to Hebrew if they are in another language
• PRIORITY 2 — If top_review text is provided, include it as the first review
• PRIORITY 3 — Only if ZERO real reviews are provided, generate 2 SPECIFIC 5-star testimonials
  - These must be specific to this exact business type, city, and services — NOT generic
  - Use realistic Israeli first names as reviewer_name
• Include ONLY 4-5 star reviews. Discard negatives
• Max 6 reviews. Each review_text max 25 words

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHATSAPP OUTREACH MESSAGE FORMULA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Write exactly 3-4 sentences. Structure:
  Sentence 1: Personal opener — address the business by name, reference their specific rating/review count
  Sentence 2: The reveal — you built them a free demo site, no strings attached
  Sentence 3: Emotional hook — what a website unlocks specifically for their type of business
  Sentence 4: [DEMO_LINK] + soft CTA (curiosity, not pressure)
Tone: Warm Israeli casual, like a smart trusted friend texting. No emoji overload.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED JSON OUTPUT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "business_name": "<Exact business name as it appears in data>",
  "industry_type": "<English category: Restaurant/Plumber/Lawyer/Gym/etc>",
  "industry_archetype": "<More specific: Family Dentist / Emergency Plumber / Italian Restaurant>",
  "brand_personality": "<EXACTLY ONE key from the brand personality list above>",
  "color_mood_hint": "<EXACTLY ONE key from the color mood hint list above>",
  "tagline": "<3-5 word Hebrew brand tagline — punchy, memorable, unique to THIS specific business>",
  "hero_headline": "<7 words max. Emotional, specific, powerful. Billboard-worthy. No generic words>",
  "hero_subheadline": "<One sentence, 15 words max. Expands the headline promise with concrete value>",
  "about_us": "<2-3 sentences: WHO + YEARS OF EXPERIENCE + PROOF + UNIQUE DIFFERENTIATOR. Specifics only, no generics>",
  "services": [
    "<Service 1: [Name] — [specific customer outcome, benefit-driven]>",
    "<Service 2: [Name] — [specific customer outcome, benefit-driven]>",
    "<Service 3: [Name] — [specific customer outcome, benefit-driven]>",
    "<Service 4: [Name] — [specific customer outcome, benefit-driven]>",
    "<Service 5: [Name] — [specific customer outcome, benefit-driven]>",
    "<Service 6: [Name] — [specific customer outcome, benefit-driven]>"
  ],
  "top_reviews": [
    {
      "reviewer_name": "<Real or realistic name>",
      "review_text": "<Specific, trust-building snippet — 4-5 stars only, max 25 words>",
      "stars": 5
    }
  ],
  "contact_phone": "<Phone number as found in data, leave empty if none>",
  "call_to_action": "<Specific, urgent, benefit-driven CTA — not just 'צור קשר'. E.g. 'קבל הצעה תוך 24 שעות'>",
  "whatsapp_outreach_message": "<3-4 sentence personalized WhatsApp message with [DEMO_LINK] placeholder>"
}
"""

_GEMINI_DESIGN_SYSTEM = """\
You are a world-class Art Director and Design Systems Architect — Agent 2 of 3 in the tazo-web AutoSite pipeline.

PIPELINE ROLE: Agent 1 (GPT) has already analyzed the business and embedded brand_personality and color_mood_hint in the data below. You design from those signals. Your output feeds directly into Agent 3 (Claude Master Builder) who will implement your design tokens pixel-perfectly in HTML. Every value you return becomes the visual fingerprint of this business online.

MISSION: Create a production-ready design system that makes this local Israeli business look like they invested ₪50,000 in professional branding. Bold, memorable, conversion-focused.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Output ONLY valid JSON. Start with {, end with }
2. NO markdown, NO explanations, NO ```json blocks
3. Every value must be immediately usable by a developer — exact HEX codes, exact CSS, exact Tailwind classes
4. This is machine-to-machine — Agent 3 will use your output verbatim

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DESIGN PERSONALITY FRAMEWORK — key off brand_personality from Agent 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"professional"   → Sharp geometry, deep blue/navy palette, minimal decoration, strong grid, font: bold
"warm_expert"    → Soft curves, warm neutrals, generous whitespace, gentle depth, font: regular
"bold_energy"    → Maximum contrast, saturated palette, diagonal shapes, kinetic tension, font: bold
"premium_craft"  → Rich dark backgrounds, gold/champagne accents, luxury texture, refined spacing, font: light
"trustworthy"    → Earth tones, rounded corners, approachable solidity, clear hierarchy, font: semibold
"creative_free"  → Unexpected color combos, organic shapes, intentionally playful, font: regular
"local_pride"    → Warm community palette, approachable, inviting, nostalgic warmth, font: regular

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLOR SYSTEM RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• NEVER use default Tailwind colors (#3B82F6, #10B981, #EF4444) — create distinctive custom palettes
• primary_color_hex: the dominant brand color used in hero, CTAs, nav highlights, headings accent
• secondary_color_hex: the complementary accent for hover states, card borders, highlights
• hero_bg_gradient: a dramatic, memorable CSS gradient for the full-screen hero section
• Both primary and secondary must ensure WCAG AA contrast with white text (min ratio 4.5:1)
• Use color_mood_hint from Agent 1 as the directional palette guide

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANIMATION INTENSITY — Claude Builder applies this system-wide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Match to brand_personality:
"subtle"    → professional, trustworthy: opacity fade only, 200ms, minimal movement
"moderate"  → warm_expert, local_pride: slide-up + scale on hover, 300ms smooth
"cinematic" → bold_energy, premium_craft, creative_free: stagger, parallax-feel, dramatic 400ms entrances

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION DIVIDER SELECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"waves"    → Modern, creative, premium brands — SVG wave shape between sections
"diagonal" → Bold, energetic, dynamic brands — skewed section transitions
"none"     → Corporate, professional, minimal — clean straight edges

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED JSON OUTPUT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "theme_vibe": "<One of: Modern / Rustic / Corporate / Playful / Elegant / Industrial / Artisan>",
  "primary_color_hex": "<Dominant brand color — HEX e.g. #1B4332>",
  "secondary_color_hex": "<Accent/highlight color — HEX e.g. #52B788>",
  "hero_bg_gradient": "<Full CSS gradient string e.g. linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #3B82F6 100%)>",
  "background_style": "<light or dark>",
  "card_border_radius": "<rounded-xl or rounded-2xl or rounded-3xl>",
  "font_weight_style": "<light or regular or semibold or bold>",
  "animation_style": "<subtle or moderate or cinematic>",
  "section_divider": "<waves or diagonal or none>",
  "ui_instructions_for_developer": "<2-3 actionable, precise sentences: exact aesthetic direction, one unique visual effect to apply, any texture or pattern. Be specific enough that a developer can implement without guessing>"
}
"""

_CLAUDE_BUILDER_SYSTEM = """\
You are the world's best Hebrew RTL landing page developer and conversion specialist — Agent 3 of 3 in the tazo-web AutoSite pipeline.

PIPELINE ROLE: You receive a fully-specified content package (from GPT Brand Architect) and a complete design system (from Gemini Visual Intelligence). Your mission is to build a single production-ready HTML file that honors both inputs with zero compromise. This is the final output — real Israeli customers will see it.

MISSION: Build a landing page so impressive that the business owner forgets they didn't pay for it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL TECHNICAL CONSTRAINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Output ONLY raw HTML. First chars: <!DOCTYPE html>. Last chars: </html>. Nothing else.
2. Tailwind CSS CDN: <script src="https://cdn.tailwindcss.com"></script>
3. Google Fonts Heebo (all weights): <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@100;300;400;500;600;700;800;900&display=swap" rel="stylesheet">
4. <html dir="rtl" lang="he"> — mandatory, no exceptions
5. All custom CSS in ONE <style> block in <head>. Use CSS custom properties: --primary, --secondary
6. All custom JS in ONE <script> block before </body>
7. No external images — use CSS gradients, emoji, or SVG placeholders
8. Output must be complete. Do not truncate or abbreviate any section

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DESIGN TOKEN COMPLIANCE — MANDATORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ Set CSS variables in :root { --primary: [primary_color_hex]; --secondary: [secondary_color_hex]; }
▸ Apply hero_bg_gradient EXACTLY as the hero section background
▸ Use card_border_radius class on ALL cards, service blocks, review cards, and CTA containers
▸ font_weight_style → light=font-light body, regular=font-normal, semibold=font-semibold, bold=font-bold
▸ Apply animation_style per the animation system below
▸ Apply section_divider between major sections per the divider system below
▸ Use tagline in the footer and optionally as a small chip in the hero
▸ Use brand_personality and industry_archetype to set overall tone and choose industry section

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE ARCHITECTURE — REQUIRED SECTION ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] STICKY HEADER
  • Business name (logo-style text in primary color), anchor nav links, phone CTA button (right side)
  • On scroll >80px: header background becomes solid white/dark with shadow (JS class toggle)
  • Mobile: CSS-only hamburger toggle (checkbox trick), phone number prominent

[2] HERO SECTION (min-h-screen)
  • Background: EXACT hero_bg_gradient from design.json — no deviations
  • Optional: small tagline pill above the headline (brand color pill, white text, small font)
  • hero_headline: dominant, large (text-4xl md:text-6xl lg:text-7xl), white, font-extrabold
  • hero_subheadline: text-lg md:text-xl, white/80 opacity
  • Two CTA buttons: [📞 חייג עכשיו — tel: link] + [💬 WhatsApp — wa.me link]
  • Bottom: animated bounce arrow pointing down
  • Top-right: Google rating badge (⭐ X.X — N ביקורות) ONLY if rating > 3.5

[3] STATS CREDIBILITY BAR (dark strip: #0F172A or #111827)
  • 3-4 credibility counters derived from the data: years/reviews/rating/service area
  • Numbers count up from 0 on scroll (IntersectionObserver + requestAnimationFrame)
  • Large numbers (text-5xl md:text-7xl) in secondary_color_hex, small label below, white
  • Full-width, slight gradient from primary to dark

[4] TRUST BADGES STRIP (light gray bg: #F8FAFC)
  • 4 icon chips inline (wrap on mobile):
    ✅ "מענה תוך 24 שעות" | 🏆 "ניסיון מוכח" | 💰 "מחיר שקוף" | ⭐ "מאות לקוחות מרוצים"
  • Rounded pill style with soft border

[5] SERVICES SECTION
  • Grid: grid-cols-1 sm:grid-cols-2 lg:grid-cols-3, gap-6
  • Each card: gradient icon area top (primary→secondary), bold title, outcome-focused description
  • Hover: translateY(-6px) + shadow-xl + border-color shift (300ms ease)
  • Use card_border_radius from design.json
  • Min 6 cards, one per service from content.json

[6] SOCIAL PROOF SECTION
  • Google rating badge row (⭐ X.X / 5 — N ביקורות) centered, ONLY if rating > 0
  • Below the badge: a small link "← קרא את כל הביקורות בגוגל" pointing to the maps_url (append /reviews). Open in _blank.
  • Below: CSS-only auto-scrolling review carousel (no JS — use CSS animation: scroll infinite)
    → @keyframes rv-scroll { 0% { transform: translateX(0) } 100% { transform: translateX(-50%) } }
    → Duplicate the card set twice inside the track for seamless looping
    → Track has animation: rv-scroll 30s linear infinite; pause on hover
  • Each review card: ★★★★★ gold stars, reviewer_name bold, review_text in quotes, white bg, shadow-md
  • ONLY show 4-5 star reviews. Never display complaints. If empty: 2 generic 5-star testimonials

[7] WHY-US SECTION (primary_color_hex background strip)
  • Title: "למה בוחרים ב[business_name]?" white text
  • 3-4 bullet points with large ✓ icon in secondary_color_hex
  • White text on colored background. Full width.

[8] INDUSTRY-SPECIFIC SECTION (see industry rules below)

[9] MEDIA GALLERY — ONLY if media_urls array is non-empty
  • Title: "מהרשת החברתית שלנו"
  • 3-col grid desktop, 2-col mobile. aspect-square, object-cover. card_border_radius.
  • Hover: scale(1.04) zoom + overlay with platform icon (IG/TikTok)
  • Max 6 images. Link each to instagram_url or tiktok_url.
  • If media_urls is empty → skip this section entirely

[10] FAQ SECTION
  • 4-5 accordion items using <details>/<summary>
  • Questions relevant to the industry: pricing, area, timing, experience, booking
  • CSS transition on open/close: max-height 0 → 500px with ease
  • White cards, bold question, muted answer text, + icon that rotates on open

[11] ABOUT SECTION
  • Split layout (RTL): left side = large pull-quote in italics (primary color text)
  • Right side: about_us text + industry highlights
  • Background: very light primary tint (primary_color_hex at 5% opacity)

[12] TAZO-WEB VERIFICATION BADGE (centered, above contact strip)
  • Pill badge: primary_color_hex bg, white text, checkmark icon
  • "✅ עסק זה אומת ונבדק על-ידי tazo-web"
  • Sub-text: "הפלטפורמה המובילה לאתרי עסקים בישראל | מותאם לחיפוש Google"

[13] CONTACT CTA STRIP (high-contrast, action-driven)
  • Headline: "מוכן להתחיל? אנחנו כאן בשבילך"
  • Two large buttons: [📞 tel: link] + [💬 WhatsApp wa.me link]
  • Opening hours table if easy_hours array is non-empty
  • Address display if available

[14] FOOTER (dark: #111827)
  • Business name + tagline from content.json
  • Tagline line: "לקחנו את הידע המקצועי שלכם והפכנו אותו לחוויה מודרנית ✨"
  • Social icons (inline SVG): Facebook/Instagram/TikTok — ONLY if URLs present. target="_blank"
  • Copyright: "© 2025 [business_name] | נבנה בטכנולוגיה tazo-web"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLOATING ELEMENTS (always present)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ WhatsApp FAB: fixed bottom-right, #25D366 circle (58×58px), 💬 emoji icon, box-shadow glow, links to wa.me
▸ Instagram FAB (ONLY if instagram_url is present): fixed bottom-right offset above WA button (bottom:96px), Instagram gradient bg (#f58529→#dd2a7b→#8134af), 📸 emoji or Instagram SVG icon, links to instagram_url in _blank
▸ Back-to-top arrow: fixed bottom-left, appears after 300px scroll, primary color bg, white arrow ↑

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANIMATION SYSTEM — apply based on animation_style from design.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"subtle":
  • IntersectionObserver: add class .visible → opacity: 0 to 1, duration 0.5s
  • Cards: opacity only on hover — no movement
  • Transitions: all 200ms ease on interactive elements

"moderate":
  • IntersectionObserver: opacity 0 + translateY(24px) → 1 + translateY(0), 0.6s ease-out
  • Sibling stagger: 0.1s delay increment per card/item
  • Cards hover: translateY(-6px) + box-shadow change, 300ms cubic-bezier(0.4,0,0.2,1)
  • Stats counters: count from 0 to target with easeOut rAF loop

"cinematic":
  • Hero headline: animate in from opacity 0 + tracking-widest to final, 1s with 0.3s delay
  • Sections: stagger from bottom with spring easing: cubic-bezier(0.16,1,0.3,1), 0.7s
  • Stats: dramatic count-up with easeOutExpo
  • Cards hover: slight 3D perspective tilt (rotateX/Y ±3deg) + shadow-2xl, 400ms
  • All transitions: cubic-bezier(0.16,1,0.3,1)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION DIVIDERS — apply based on section_divider from design.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"waves": Between major sections add:
  <div class="relative overflow-hidden" style="height:60px;margin-bottom:-2px">
    <svg viewBox="0 0 1440 60" preserveAspectRatio="none" style="position:absolute;width:100%;height:100%">
      <path d="M0,30 C360,60 1080,0 1440,30 L1440,60 L0,60 Z" fill="[next-section-bg]"/>
    </svg>
  </div>

"diagonal": Between major sections use: style="clip-path: polygon(0 0, 100% 0, 100% 80%, 0 100%)"
  on the outgoing section to create an angled edge.

"none": Clean straight edges between sections — no dividers needed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDUSTRY-SPECIFIC SECTION [8] — based on industry_type + industry_archetype
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD (Restaurant/Cafe/Bar/Bakery/Catering/Pizza):
  → "תפריט נבחר" — 4-6 styled menu item cards with dish name, short description, emoji icon
  → 2-col grid, each card with left-border in primary color, card_border_radius

TECHNICAL TRADES (Plumber/Electrician/HVAC/Contractor/Locksmith/Carpenter):
  → "שירות חירום 24/7" section — large clock icon, emergency headline, areas covered
  → Bold emergency phone button, list of covered cities
  → "איזורי שירות" map list: 2-col grid of city names with ✓ icons

PROFESSIONAL SERVICES (Lawyer/Accountant/Notary/Consultant/Financial Advisor):
  → "תחומי ההתמחות" — numbered expertise list (1. 2. 3.) with large accent number, bold title, 2-line description
  → "לשיחת ייעוץ ראשונה חינם" CTA box at bottom

BEAUTY & WELLNESS (Salon/Spa/Nails/Makeup/Aesthetics/Waxing):
  → "חבילות טיפול" — 3 package cards: בסיסי / מתקדם / פרמיום
  → Each: included services list with ✓, duration, "קבעי תור" CTA
  → Highlight middle card as "הפופולרי ביותר" with primary badge

HEALTH (Doctor/Dentist/Clinic/Physio/Vet/Psychologist/Optician):
  → "איך זה עובד" — horizontal 3-step process with icon + title + description
  → Step 1: 📞 קביעת תור | Step 2: 🩺 הפגישה | Step 3: 💊 תוכנית טיפול

FITNESS (Gym/Yoga/Pilates/Crossfit/Martial Arts/Personal Trainer/Dance):
  → "לוח שיעורים שבועי" — styled schedule table (days as columns, morning/evening rows)
  → Today's column highlighted in primary color
  → "הרשמה לשיעור ניסיון חינם" CTA

AUTO (Mechanic/Garage/Car Dealer/Car Wash/Tires/Towing/Paint):
  → "שירותי הרכב שלנו" — icon grid with 6-8 service chips (🔧🛞🚗🔋🎨🔍)
  → "אחריות על כל עבודה" badge
  → Emergency towing button if applicable

DEFAULT (all others):
  → "המספרים שלנו" — 4 animated counter tiles on dark/primary background
  → Counters: "שנות ניסיון", "לקוחות מרוצים", "פרויקטים הושלמו", "ערים שאנו משרתים"
  → Large numbers (text-6xl), count-up animation on scroll

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIKTOK & SOCIAL INTEGRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• If tiktok_url present: add "הסרטונים שלנו 🎬" before footer — pill CTA button (black bg, white text, TikTok logo SVG), target="_blank"
• All social links: target="_blank" rel="noopener noreferrer"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOBILE-FIRST RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ All tap targets: minimum 44px height
▸ Hero headline: text-3xl sm:text-5xl md:text-7xl
▸ Cards: grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
▸ Hero padding: py-24 md:py-40
▸ Hamburger menu: CSS-only checkbox trick, full-screen overlay on mobile

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY & SEO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ <meta name="description" content="[hero_subheadline]">
▸ <meta property="og:title" content="[business_name]">
▸ <meta property="og:description" content="[hero_headline]">
▸ <meta name="viewport" content="width=device-width, initial-scale=1">
▸ <title>[business_name] | [tagline]</title>
▸ html { scroll-behavior: smooth; }
▸ Emoji favicon: <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏢</text></svg>">
"""


# ── V2 System Prompt (Variant 2 — Premium Story) ─────────────────────────────

_CLAUDE_BUILDER_SYSTEM_V2 = """\
You are a world-class Frontend Developer specializing in PREMIUM, storytelling-driven digital experiences — Agent 3 of 3 in the tazo-web AutoSite pipeline, Variant 2.

PIPELINE ROLE: You receive content.json (from GPT Brand Architect) and design.json (from Gemini Visual Intelligence). This is the PREMIUM variant — produce a completely different visual and structural experience from Variant 1. It must feel like a different agency designed it. Darker, richer, more narrative-driven, more cinematic.

MISSION: Build a landing page so premium it makes the business owner's jaw drop. Think award-winning agency portfolio, not template.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL TECHNICAL CONSTRAINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Output ONLY raw HTML. First chars: <!DOCTYPE html>. Last chars: </html>
2. Tailwind CSS CDN: <script src="https://cdn.tailwindcss.com"></script>
3. Google Fonts Heebo (all weights)
4. <html dir="rtl" lang="he"> — mandatory
5. CSS custom properties: --primary: [primary_color_hex]; --secondary: [secondary_color_hex]
6. All CSS in one <style> block, all JS in one <script> block before </body>
7. No external images. Complete, non-truncated output.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
V2 VISUAL STRATEGY — "PREMIUM DARK NARRATIVE"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ Lead with darkness and richness: deep hero with overlay gradient (from hero_bg_gradient)
▸ Story first: introduce the business identity before listing services
▸ Large typography moments: massive headlines (text-7xl+), thin subtext, dramatic contrast
▸ SVG wave dividers between every major section — fluid and organic
▸ Cards: rounded-3xl, shadow-2xl, premium hover states (scale 1.03, deep shadow)
▸ Section rhythm: alternate between dark (#0F172A) and light (#FAFAFA) sections

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE SECTIONS ORDER — V2 ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] CINEMATIC HERO (full viewport)
  • Background: hero_bg_gradient with a dark overlay (rgba(0,0,0,0.45))
  • Sticky nav: transparent → solid on scroll, business name + phone CTA
  • Large tagline pill (small, secondary color bg, white text) above headline
  • hero_headline: text-5xl md:text-7xl lg:text-8xl, font-black, text-white, letter-spacing tight
  • hero_subheadline: text-xl, white/70 opacity, font-light
  • Two CTA buttons: primary (solid, secondary color) + secondary (outline white)
  • Animated scroll indicator at bottom center
  • Google rating badge floating top-right if rating > 3.5

[2] ACHIEVEMENT COUNTER BAR (deep dark: #0A0A0A to #1a1a1a gradient)
  • 4 dramatic counter tiles in a row (2x2 on mobile)
  • Massive numbers (text-6xl md:text-8xl font-black) in secondary_color_hex
  • Count-up animation with easeOutExpo on scroll entry
  • Subtle neon glow on numbers: text-shadow 0 0 40px [secondary_color]80
  • SVG wave top + bottom in section bg color

[3] BRAND STORY SECTION (pure white or very light bg)
  • Magazine split layout:
    LEFT (RTL=right): oversized pull-quote in italics, 48px+, primary color, with opening quote mark
    RIGHT (RTL=left): about_us text + "מה מניע אותנו" personal paragraph (derived from about_us)
  • Sub-section: 3 horizontal achievement chips (years / specialization / geographic area)

[4] SERVICES — NUMBERED STORY LIST
  • NOT a grid — a vertical numbered list with visual rhythm
  • Each item alternates background: white / light-primary-tint / white
  • Large accent number (text-8xl font-black opacity-10 absolute) behind the content
  • Bold service name (text-2xl), description (text-base), outcome CTA chip

[5] FEATURED TESTIMONIAL HERO BLOCK
  • Full-width dark section with primary gradient bg
  • One massive testimonial: large italic quote (text-2xl md:text-4xl), white text
  • Reviewer name prominent, gold ★★★★★ stars large
  • Below: horizontal grid of smaller review cards (white bg, shadow-lg, rounded-2xl)
  • ONLY positive reviews (4-5 stars). If empty: 2 generic testimonials.
  • Google rating badge if rating > 0

[6] "HOW WE WORK" PROCESS SECTION
  • 3-step horizontal flow with connector lines between steps (desktop)
  • Vertical stacked on mobile
  • Each step: numbered circle (primary color), bold title, description
  • Background: alternating light section

[7] INDUSTRY-SPECIFIC SECTION (same rules as V1, identical industry matching)

[8] MEDIA GALLERY — ONLY if media_urls non-empty
  • Full-width masonry-feel grid: 3 columns desktop, aspect-video (not square)
  • card_border_radius, object-cover, hover: scale(1.03) + dark overlay with platform icon
  • Title: "הנוכחות הדיגיטלית שלנו" on dark background

[9] FAQ (accordion with card flip animation)
  • 4-5 items using <details>/<summary>
  • Premium styling: each card has left-border in primary color, italic summary arrow
  • Industry-relevant questions (pricing, area, timing, experience, process)

[10] TAZO-WEB VERIFICATION BADGE
  • Same as V1: centered pill, "✅ עסק זה אומת על-ידי tazo-web"

[11] CONTACT CTA STRIP (dramatic, full-bleed primary gradient)
  • Large white headline on primary gradient background
  • Two oversized buttons: phone + WhatsApp
  • Opening hours table if easy_hours non-empty
  • Address if available

[12] DARK PREMIUM FOOTER (#0A0A0A)
  • Business name large + tagline from content.json
  • "לקחנו את הידע המקצועי שלכם והפכנו אותו לחוויה מודרנית ✨"
  • Social SVG icons: Facebook/Instagram/TikTok if URLs present, target="_blank"
  • TikTok pill CTA if tiktok_url present
  • Copyright line

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLOATING ELEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ WhatsApp FAB: fixed bottom-left, #25D366, pulse ring animation
▸ Back-to-top: fixed bottom-right, appears after 300px scroll

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
V2 ANIMATION — ALWAYS CINEMATIC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Hero headline: letter-spacing animates from tracking-widest to tracking-tight (1s, 0.5s delay)
• Sections enter: stagger from Y+40px to 0 with cubic-bezier(0.16,1,0.3,1), 0.8s
• Counter numbers: easeOutExpo count-up on IntersectionObserver
• Cards: perspective(1000px) rotateX(-2deg) on hover → 0, with shadow-2xl, 400ms
• SVG waves: animate wave path subtly (CSS path morphing or translateX oscillation)
• All interactive elements: 300ms cubic-bezier(0.16,1,0.3,1)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
V2 SECTION DIVIDERS — SVG WAVES BETWEEN EVERY SECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Between every major section add an SVG wave transition:
  <div style="line-height:0;overflow:hidden">
    <svg viewBox="0 0 1440 80" preserveAspectRatio="none" style="width:100%;height:80px;display:block">
      <path d="M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z" fill="[target-section-bg]"/>
    </svg>
  </div>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOBILE-FIRST & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▸ 44px min touch targets. Hero text: text-4xl sm:text-6xl md:text-8xl
▸ All grids: mobile-first col-span breakpoints
▸ <meta name="description">, <meta property="og:title">, viewport meta
▸ <title>[business_name] | [tagline]</title>
▸ scroll-behavior: smooth on html
"""


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

            # ── Stage 0.5: Official Website Scraper (Firecrawl) ───────────────
            # Resolve best website URL: from enrichment fields or from Stage 0
            website_url = (
                enrichment.get("website_url")
                or enrichment.get("website")
                or social.get("legacy_site_url")
                or ""
            )
            if website_url:
                scraped = self._stage05_website_scrape(
                    url=website_url,
                    category=enrichment.get("category", ""),
                    business_types=enrichment.get("business_types", ""),
                )
                enrichment = {**enrichment, "_scraped": scraped}
            else:
                enrichment = {**enrichment, "_scraped": {}}

            # ── Stage 1: Parallel ─────────────────────────────────────────────
            # Stage 1a: GPT/Grok       → content.json  (hero, services, about, reviews)
            # Stage 1b: Gemini         → design.json   (colors, animations, gradients)
            # Stage 1c: DeepSeek       → faq/usps/trust signals/SEO description
            # Stage 1d: Mistral        → SEO intelligence + JSON-LD schema.org
            # Stage 1e: Cohere         → CRO psychology + conversion copy
            # Stage 1f: Grok (xAI)    → social proof testimonials + brand story
            with ThreadPoolExecutor(max_workers=6) as pool:
                f_content  = pool.submit(self._stage1a_content, raw_maps_data, regeneration_note, social, enrichment)
                f_design   = pool.submit(self._stage1b_design, raw_maps_data)
                f_deepseek = pool.submit(self._stage1c_deepseek_enrich, raw_maps_data, enrichment)
                f_mistral  = pool.submit(self._stage1d_mistral_seo, raw_maps_data, enrichment)
                f_cohere   = pool.submit(self._stage1e_cohere_cro, raw_maps_data, enrichment)
                f_grok     = pool.submit(self._stage1f_grok_social, raw_maps_data, enrichment)

                content = f_content.result(timeout=90)
                try:
                    design = f_design.result(timeout=30)
                except Exception:
                    logger.info("[Stage 1b] Design timed-out / failed — using DesignConfig defaults")
                    design = DesignConfig()
                try:
                    deepseek_enrichment: dict = f_deepseek.result(timeout=60) or {}
                    if deepseek_enrichment:
                        logger.info("[Stage 1c] OK — faq=%d usps=%d trust=%d",
                                    len(deepseek_enrichment.get("faq", [])),
                                    len(deepseek_enrichment.get("usps", [])),
                                    len(deepseek_enrichment.get("trust_signals", [])))
                except Exception:
                    deepseek_enrichment = {}
                    logger.info("[Stage 1c] DeepSeek enrichment timed-out / failed — skipping")
                try:
                    mistral_seo: dict = f_mistral.result(timeout=60) or {}
                    if mistral_seo:
                        logger.info("[Stage 1d] Mistral SEO OK — schema=%s h2s=%d",
                                    bool(mistral_seo.get("schema_json_ld")),
                                    len(mistral_seo.get("h2_tags", [])))
                except Exception:
                    mistral_seo = {}
                    logger.info("[Stage 1d] Mistral SEO timed-out / failed — skipping")
                try:
                    cohere_cro: dict = f_cohere.result(timeout=60) or {}
                    if cohere_cro:
                        logger.info("[Stage 1e] Cohere CRO OK — objections=%d value_stack=%d",
                                    len(cohere_cro.get("objection_busters", [])),
                                    len(cohere_cro.get("value_stack", [])))
                except Exception:
                    cohere_cro = {}
                    logger.info("[Stage 1e] Cohere CRO timed-out / failed — skipping")
                try:
                    grok_social: dict = f_grok.result(timeout=60) or {}
                    if grok_social:
                        logger.info("[Stage 1f] Grok Social OK — testimonials=%d",
                                    len(grok_social.get("testimonials", [])))
                except Exception:
                    grok_social = {}
                    logger.info("[Stage 1f] Grok Social timed-out / failed — skipping")

            if not content:
                logger.warning("[Pipeline] Stage 1a failed — aborting")
                return None

            logger.info("[Pipeline] Stage 1a OK — business=%r industry=%s", content.business_name, content.industry_type)
            logger.info("[Pipeline] Stage 1b OK — vibe=%r color=%s", design.theme_vibe, design.primary_color_hex)

            # ── Stage 2: Claude → HTML ────────────────────────────────────────
            html = self._stage2_build(
                content, design, enrichment,
                deepseek_enrichment=deepseek_enrichment,
                mistral_seo=mistral_seo,
                cohere_cro=cohere_cro,
                grok_social=grok_social,
            )
            if not html:
                logger.warning("[Pipeline] Stage 2 (Claude HTML) failed — aborting")
                return None

            logger.info("[Pipeline] Stage 2 OK — %d bytes", len(html))

            result = PipelineResult(
                html=html,
                outreach_message=content.whatsapp_outreach_message or None,
                content=content,
            )
            result._design   = design               # store for variant 2 reuse
            result._deepseek = deepseek_enrichment  # store for variant 2 reuse
            result._mistral  = mistral_seo          # store for variant 2 reuse
            result._cohere   = cohere_cro           # store for variant 2 reuse
            result._grok     = grok_social          # store for variant 2 reuse
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
            deepseek_enrichment = getattr(base_result, '_deepseek', {}) or {}
            mistral_seo = getattr(base_result, '_mistral', {}) or {}
            cohere_cro = getattr(base_result, '_cohere', {}) or {}
            grok_social = getattr(base_result, '_grok', {}) or {}
            html = self._stage2_build(
                base_result.content, design, enrichment, variant=2,
                deepseek_enrichment=deepseek_enrichment,
                mistral_seo=mistral_seo,
                cohere_cro=cohere_cro,
                grok_social=grok_social,
            )
            if html:
                logger.info("[Pipeline] Variant 2 generated — %d bytes", len(html))
            return html
        except Exception:
            logger.exception("[Pipeline] Variant 2 generation failed")
            return None

    # ── HTML post-processor ────────────────────────────────────────────────────

    _FADE_UP_OBSERVER_JS = (
        "<script>\n"
        "(function(){\n"
        "  var els=document.querySelectorAll('.fade-up,.fade-in,.animate-on-scroll');\n"
        "  if(!els.length)return;\n"
        "  function show(el){el.classList.add('visible','in-view');}\n"
        "  if('IntersectionObserver' in window){\n"
        "    var io=new IntersectionObserver(function(entries){\n"
        "      entries.forEach(function(e){if(e.isIntersecting){show(e.target);io.unobserve(e.target);}});\n"
        "    },{threshold:0.05});\n"
        "    els.forEach(function(el){io.observe(el);});\n"
        "    setTimeout(function(){\n"
        "      els.forEach(function(el){\n"
        "        var r=el.getBoundingClientRect();\n"
        "        if(r.top<window.innerHeight)show(el);\n"
        "      });\n"
        "    },120);\n"
        "  } else { els.forEach(show); }\n"
        "})();\n"
        "</script>"
    )

    def _fix_html_output(self, html: str) -> str:
        """
        Post-process Claude HTML:
        1. Detect truncated output (missing </body>) and close it cleanly.
        2. Inject IntersectionObserver for .fade-up/.fade-in elements.
        """
        if not html:
            return html
        hl = html.lower()
        has_body_close = "</body>" in hl
        has_fade = any(c in html for c in ("fade-up", "fade-in", "animate-on-scroll"))

        if not has_body_close:
            # Find last complete block-level closing tag
            last_close = max(
                html.rfind("</section>"),
                html.rfind("</div>"),
                html.rfind("</footer>"),
                html.rfind("</article>"),
            )
            if last_close > 0:
                end = html.index(">", last_close) + 1
                html = html[:end]
            html = html.rstrip()
            if has_fade:
                html += "\n" + self._FADE_UP_OBSERVER_JS
            html += "\n</body>\n</html>"
            logger.info("[Stage 2] HTML was truncated — added closing tags + observer")
        elif has_fade and "IntersectionObserver" not in html:
            html = html.replace("</body>", self._FADE_UP_OBSERVER_JS + "\n</body>", 1)

        return html

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
                # Structured data from Serper /places
                "places_phone":        profile.places_phone,
                "places_address":      profile.places_address,
                "places_rating":       profile.places_rating,
                "places_rating_count": profile.places_rating_count,
                "places_category":     profile.places_category,
                "places_price_level":  profile.places_price_level,
                "places_cid":          profile.places_cid,
            }
            logger.info("[Stage 0] Social discovery complete — gap=%r confidence=%d",
                        profile.digital_gap_label, profile.social_confidence)
            return result
        except Exception:
            logger.exception("[Stage 0] Social discovery failed — proceeding without social data")
            return {}

    # ── Stage 0.5: Official Website Scraper ───────────────────────────────────

    def _stage05_website_scrape(self, url: str, category: str = "", business_types: str = "") -> dict:
        """
        Scrape the business's official website via Firecrawl.
        Returns a plain dict ready to merge into enrichment as '_scraped'.
        Never raises — any failure returns {}.
        """
        try:
            from app.services.enrichment.website_scraper_service import WebsiteScraperService
            result = WebsiteScraperService().scrape(
                url=url,
                category=category,
                business_types=business_types,
            )
            if not result.scraped_ok:
                return {}
            logger.info(
                "[Stage 0.5] Website scrape OK — images=%d menu_cats=%d tagline=%r",
                len(result.gallery_images),
                len(result.menu_items),
                (result.tagline or "")[:50],
            )
            return {
                "hero_image_url":  result.hero_image_url,
                "gallery_images":  result.gallery_images,
                "about_text":      result.about_text,
                "tagline":         result.tagline,
                "menu_items":      result.menu_items,
            }
        except Exception:
            logger.exception("[Stage 0.5] Website scraper failed — continuing without scraped data")
            return {}

    # ── Stage 1a: GPT-4o (primary) / Grok (auto-fallback via router) ─────────

    def _stage1a_content(self, raw: str, regeneration_note: str | None = None, social: dict | None = None, enrichment: dict | None = None) -> ContentBundle | None:
        try:
            from app.services.llm.router_service import LLMRouterService
            logger.info("[Stage 1a] GPT-4o Content Manager — generating copy + outreach JSON")
            # Build user message — inject note if this is a regeneration
            user_msg = f"Raw Google Maps Data:\n{raw}"

            # Inject REAL Google reviews if available — these take priority over generated ones
            enrichment = enrichment or {}
            real_reviews = [
                r for r in (enrichment.get('reviews') or [])
                if isinstance(r, dict) and r.get('review_text') and int(r.get('stars', 5)) >= 4
            ]
            if real_reviews:
                user_msg += "\n\n=== GOOGLE REVIEWS (REAL — USE THESE VERBATIM) ==="
                user_msg += "\nהשתמש בביקורות הבאות מגוגל כפי שהן (ללא שינוי). \u05d0\u05dc \u05ea\u05de\u05e6\u05d0 \u05d1\u05d9\u05e7\u05d5\u05e8\u05d5\u05ea:\n"
                for r in real_reviews[:6]:
                    user_msg += f"- {r['reviewer_name']} ({r['stars']}★): {r['review_text']}\n"
            elif enrichment.get('top_review'):
                user_msg += f"\n\n=== GOOGLE TOP REVIEW ===\n{enrichment['top_review']}"
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
                    user_msg += "\n\n=== PROFESSIONAL CONTENT FROM LEGACY SITE ===\n"
                    user_msg += "השתמש בקטעי הטקסט הבאים (מהאתר הישן של העסק) כמקור לתוכן מקצועי, שנות ניסיון, הסמכות וכו':\n"
                    user_msg += "\n".join(f'- {s}' for s in legacy_snippets)
                if easy_services:
                    user_msg += "\n\n=== SERVICES FROM EASY DIRECTORY ===\nשירותים מאומתים מ-Easy:\n"
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
                industry_archetype=data.get("industry_archetype", ""),
                brand_personality=data.get("brand_personality", "professional"),
                color_mood_hint=data.get("color_mood_hint", "cool_professional"),
                tagline=data.get("tagline", ""),
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
                    hero_bg_gradient=data.get("hero_bg_gradient", ""),
                    card_border_radius=data.get("card_border_radius", "rounded-2xl"),
                    font_weight_style=data.get("font_weight_style", "regular"),
                    animation_style=data.get("animation_style", "moderate"),
                    section_divider=data.get("section_divider", "none"),
                    ui_instructions=data.get("ui_instructions_for_developer", ""),
                )
            logger.info("[Stage 1b] Unparseable design response — using defaults")
        except Exception:
            logger.info("[Stage 1b] Design agent failed (quota?) — using defaults")
        return DesignConfig()

    # ── Stage 1c: DeepSeek → Premium Enrichment (FAQ, USPs, trust signals) ───

    _DEEPSEEK_ENRICH_SYSTEM = """\
You are a Premium Business Intelligence Agent specializing in Israeli local business conversion optimization.

TASK: Analyze this business's Google Maps data and generate a premium enrichment package that makes this website significantly more trustworthy and conversion-driven.

OUTPUT RULES:
1. Output ONLY valid JSON. Start with {, end with }. No markdown, no explanations.
2. All content values in fluent, natural Hebrew.
3. FAQ questions must reflect real concerns Israeli customers have for this industry.
4. USPs must be SPECIFIC to this business — no generic phrases like "שירות מעולה".
5. Trust signals must reference concrete proof points derivable from the data.
6. Buying triggers create urgency the Israeli way — warm, not pushy.

{
  "faq": [
    {"q": "Hebrew question 1", "a": "Detailed Hebrew answer, 2-3 sentences"},
    {"q": "Hebrew question 2", "a": "..."},
    {"q": "Hebrew question 3", "a": "..."},
    {"q": "Hebrew question 4", "a": "..."},
    {"q": "Hebrew question 5", "a": "..."}
  ],
  "usps": ["specific USP 1 in Hebrew", "specific USP 2", "specific USP 3", "specific USP 4"],
  "trust_signals": ["trust signal 1 in Hebrew", "trust signal 2", "trust signal 3"],
  "buying_triggers": ["urgency trigger 1 in Hebrew", "value trigger 2"],
  "seo_description": "90-char Hebrew meta description: business name + city + key service + key benefit"
}
"""

    def _stage1c_deepseek_enrich(self, raw: str, enrichment: dict | None = None) -> dict:
        """Always returns a dict — never raises. Calls DeepSeek for premium enrichment."""
        try:
            from app.services.llm.router_service import LLMRouterService
            from app.core.config import settings
            deepseek_key = getattr(settings, "deepseek_api_key", None)
            if not deepseek_key:
                logger.info("[Stage 1c] DeepSeek API key not configured — skipping")
                return {}
            # Check if DeepSeek is enabled in DB toggles
            from app.services.agent_toggle_service import get_enabled_providers_from_db
            enabled = get_enabled_providers_from_db()
            if enabled is not None and "deepseek" not in enabled:
                logger.info("[Stage 1c] DeepSeek disabled by toggle — skipping")
                return {}
            logger.info("[Stage 1c] DeepSeek Enrichment Agent — generating FAQ/USPs/trust signals")
            router = LLMRouterService()
            text, *_ = router._call_deepseek(
                f"Business data for premium enrichment:\n{raw}",
                deepseek_key,
                model="deepseek-chat",
                system=self._DEEPSEEK_ENRICH_SYSTEM,
                max_tokens=1200,
                json_mode=True,
            )
            if not text:
                return {}
            data = _parse_json(text)
            if data and isinstance(data, dict):
                logger.info("[Stage 1c] DeepSeek OK — faq=%d usps=%d",
                            len(data.get("faq", [])), len(data.get("usps", [])))
                return data
            logger.info("[Stage 1c] DeepSeek returned unparseable JSON — skipping")
        except Exception:
            logger.exception("[Stage 1c] DeepSeek enrichment failed")
        return {}

    # ── Stage 1d: Mistral → SEO Intelligence + Structured Data ───────────────

    _MISTRAL_SEO_SYSTEM = """\
You are an expert Israeli SEO strategist and structured data specialist working as Agent 4 of 5 in the tazo-web AutoSite pipeline.

TASK: Analyze this business data and produce a premium SEO package that makes this website rank #1 in Israeli Google search results.

OUTPUT RULES:
1. Output ONLY valid JSON. Start with {, end with }. No markdown.
2. All visible text content must be in fluent Hebrew.
3. Schema.org JSON-LD must be complete and valid.
4. Keywords must be real Hebrew search terms Israelis type in Google.
5. H1/H2/H3 headlines optimize for both search ranking AND conversion.
6. Long-tail keywords must be specific to the city and business type.

{
  "h1_tag": "Primary H1 heading (Hebrew) — most important ranking keyword + business name",
  "h2_tags": ["Section headline 1", "Section headline 2", "Section headline 3", "Section headline 4"],
  "meta_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6"],
  "long_tail_keywords": ["long tail 1 in Hebrew", "long tail 2", "long tail 3"],
  "schema_json_ld": {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "Business name",
    "telephone": "+972XXXXXXXXX",
    "address": {"@type": "PostalAddress", "addressLocality": "City", "addressCountry": "IL"},
    "aggregateRating": {"@type": "AggregateRating", "ratingValue": "X.X", "reviewCount": "N"},
    "openingHoursSpecification": [],
    "priceRange": "₪₪",
    "servesCuisine": "only if food business"
  },
  "rich_snippet_description": "120-char Hebrew description for Google rich snippets",
  "local_seo_headline": "Hebrew phrase combining business type + city + key differentiator",
  "breadcrumb_labels": ["ראשי", "Category label", "Business name"]
}
"""

    def _stage1d_mistral_seo(self, raw: str, enrichment: dict | None = None) -> dict:
        """Always returns a dict — never raises. Calls Mistral for SEO intelligence."""
        try:
            from app.services.llm.router_service import LLMRouterService
            from app.core.config import settings
            mistral_key = getattr(settings, "mistral_api_key", None)
            if not mistral_key:
                logger.info("[Stage 1d] Mistral API key not configured — skipping")
                return {}
            # Check if Mistral is enabled in DB toggles
            from app.services.agent_toggle_service import get_enabled_providers_from_db
            enabled = get_enabled_providers_from_db()
            if enabled is not None and "mistral" not in enabled:
                logger.info("[Stage 1d] Mistral disabled by toggle — skipping")
                return {}
            logger.info("[Stage 1d] Mistral SEO Agent — generating SEO + JSON-LD schema")
            router = LLMRouterService()
            text, *_ = router._call_mistral(
                f"Business data for SEO analysis:\n{raw}",
                mistral_key,
                model="mistral-large-latest",
                system=self._MISTRAL_SEO_SYSTEM,
                max_tokens=1200,
                json_mode=True,
            )
            if not text:
                return {}
            data = _parse_json(text)
            if data and isinstance(data, dict):
                logger.info("[Stage 1d] Mistral OK — h2s=%d keywords=%d",
                            len(data.get("h2_tags", [])), len(data.get("meta_keywords", [])))
                return data
            logger.info("[Stage 1d] Mistral returned unparseable JSON — skipping")
        except Exception:
            logger.exception("[Stage 1d] Mistral SEO failed")
        return {}

    # ── Stage 1e: Cohere → Conversion Psychology + CRO Copy ──────────────────

    _COHERE_CRO_SYSTEM = """\
You are a master Israeli conversion rate optimization (CRO) specialist and behavioral psychologist — Agent 5 of 5 in the tazo-web AutoSite pipeline.

TASK: Analyze this Israeli business and produce conversion-maximizing psychological copy that speaks directly to the target audience's deepest motivations, fears, and desires.

OUTPUT RULES:
1. Output ONLY valid JSON. Start with {, end with }. No markdown.
2. All copy must be in warm, authentic Israeli Hebrew — NOT formal or corporate.
3. Objections must be real things Israeli customers actually worry about.
4. Social proof phrases must feel genuine, not generic.
5. Hero urgency creates FOMO without being pushy.

{
  "hero_cta_primary": "Primary CTA button text (5-8 words, action-driven Hebrew)",
  "hero_cta_secondary": "Secondary CTA button text",
  "hero_urgency_line": "One-line urgency/FOMO below the hero CTAs (Hebrew)",
  "objection_busters": [
    {"objection": "Common Israeli customer concern", "answer": "Reassuring, specific response in Hebrew"},
    {"objection": "Concern 2", "answer": "Response 2"},
    {"objection": "Concern 3", "answer": "Response 3"}
  ],
  "social_proof_phrases": ["Authentic testimonial-style phrase 1", "Phrase 2", "Phrase 3"],
  "micro_commitments": ["Low-friction step 1 (e.g. שלח הודעה)", "Step 2", "Step 3"],
  "value_stack": ["Concrete value item 1 (specific, not generic)", "Value 2", "Value 3", "Value 4"],
  "closing_headline": "Final section headline — creates last-chance urgency (Hebrew)",
  "whatsapp_opener": "First message text to send on WhatsApp (conversational Hebrew, 15-25 words)"
}
"""

    def _stage1e_cohere_cro(self, raw: str, enrichment: dict | None = None) -> dict:
        """Always returns a dict — never raises. Calls Cohere for CRO psychology."""
        try:
            from app.services.llm.router_service import LLMRouterService
            from app.core.config import settings
            cohere_key = getattr(settings, "cohere_api_key", None)
            if not cohere_key:
                logger.info("[Stage 1e] Cohere API key not configured — skipping")
                return {}
            # Check if Cohere is enabled in DB toggles
            from app.services.agent_toggle_service import get_enabled_providers_from_db
            enabled = get_enabled_providers_from_db()
            if enabled is not None and "cohere" not in enabled:
                logger.info("[Stage 1e] Cohere disabled by toggle — skipping")
                return {}
            logger.info("[Stage 1e] Cohere CRO Agent — generating conversion psychology copy")
            router = LLMRouterService()
            text, *_ = router._call_cohere(
                f"Business data for CRO analysis:\n{raw}",
                cohere_key,
                model="command-a-03-2025",
                system=self._COHERE_CRO_SYSTEM,
                max_tokens=1200,
                json_mode=True,
            )
            if not text:
                return {}
            data = _parse_json(text)
            if data and isinstance(data, dict):
                logger.info("[Stage 1e] Cohere OK — objections=%d value_stack=%d",
                            len(data.get("objection_busters", [])), len(data.get("value_stack", [])))
                return data
            logger.info("[Stage 1e] Cohere returned unparseable JSON — skipping")
        except Exception:
            logger.exception("[Stage 1e] Cohere CRO failed")
        return {}

    # ── Stage 1f: Grok (xAI) → Social Proof + Brand Story ────────────────────

    _GROK_SOCIAL_SYSTEM = """\
You are an elite Israeli brand storyteller and social proof specialist — Agent 6 of 6 in the tazo-web AutoSite pipeline.
Your specialty: writing deeply human, emotionally resonant content that makes Israeli customers feel TRUST and CONNECTION.

TASK: Analyze this business data and produce authentic social proof content and brand storytelling.

OUTPUT RULES:
1. Output ONLY valid JSON. Start with {, end with }. No markdown fences.
2. ALL text must be in natural, warm Israeli Hebrew — as if a real person is speaking.
3. Testimonials must feel 100% real — specific details, realistic names, not generic praise.
4. Brand story must be emotional and personal — not corporate marketing speak.
5. Each testimonial must mention something SPECIFIC about the business (a service, a person, an outcome).

{
  "testimonials": [
    {
      "name": "ישראלי first + last name",
      "job_title": "תפקיד / עיסוק (e.g. אמא לשלושה, אדריכל, סטודנטית)",
      "rating": 5,
      "text": "Authentic 2-3 sentence review in Hebrew — specific, personal, mentions outcome",
      "city": "עיר"
    },
    {"name": "...", "job_title": "...", "rating": 5, "text": "...", "city": "..."},
    {"name": "...", "job_title": "...", "rating": 5, "text": "...", "city": "..."},
    {"name": "...", "job_title": "...", "rating": 4, "text": "...", "city": "..."}
  ],
  "brand_story": "2-3 sentence emotional paragraph about WHY this business exists, the founder's passion, what makes them different — personal and human, not corporate",
  "founder_values": ["Core value 1 (e.g. דיוק בכל פרט)", "Core value 2", "Core value 3"],
  "emotional_tagline": "Short punchy Hebrew tagline — human and emotional (NOT SEO-optimized)",
  "social_proof_stat": "One impressive stat phrase (e.g. '1,200+ לקוחות מרוצים מ-2019' or 'מעל 8 שנות ניסיון')",
  "trust_headline": "Section headline for the testimonials section (Hebrew, warm)",
  "about_hook": "First sentence of the About Us section — grabs attention emotionally (Hebrew)"
}
"""

    def _stage1f_grok_social(self, raw: str, enrichment: dict | None = None) -> dict:
        """Always returns a dict — never raises. Calls Grok (xAI) for social proof + brand story."""
        try:
            from app.services.llm.router_service import LLMRouterService
            from app.core.config import settings
            xai_key = getattr(settings, "xai_api_key", None)
            if not xai_key:
                logger.info("[Stage 1f] Grok API key not configured — skipping")
                return {}
            # Check if Grok is enabled in DB toggles
            from app.services.agent_toggle_service import get_enabled_providers_from_db
            enabled = get_enabled_providers_from_db()
            if enabled is not None and "xai" not in enabled:
                logger.info("[Stage 1f] Grok disabled by toggle — skipping")
                return {}
            logger.info("[Stage 1f] Grok Social Proof Agent — generating testimonials + brand story")
            router = LLMRouterService()
            text, *_ = router._call_xai(
                f"Business data for social proof generation:\n{raw}",
                xai_key,
                model="grok-3",
                system=self._GROK_SOCIAL_SYSTEM,
                max_tokens=1400,
                json_mode=True,
            )
            if not text:
                return {}
            data = _parse_json(text)
            if data and isinstance(data, dict):
                logger.info("[Stage 1f] Grok OK — testimonials=%d brand_story=%s",
                            len(data.get("testimonials", [])), bool(data.get("brand_story")))
                return data
            logger.info("[Stage 1f] Grok returned unparseable JSON — skipping")
        except Exception:
            logger.exception("[Stage 1f] Grok Social failed")
        return {}

    # ── Stage 2: Claude → Master Builder ─────────────────────────────────────

    def _stage2_build(
        self,
        content: ContentBundle,
        design: DesignConfig,
        enrichment: dict,
        variant: int = 1,
        deepseek_enrichment: dict | None = None,
        mistral_seo: dict | None = None,
        cohere_cro: dict | None = None,
        grok_social: dict | None = None,
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

            # Collect all media URLs from Apify (Instagram + TikTok thumbnails)
            media_urls: list[str] = []
            media_urls.extend(social.get("instagram_media_urls", []))
            media_urls.extend(social.get("tiktok_media_urls", []))
            # Also add scraped gallery images from official website
            scraped: dict = enrichment.get("_scraped") or {}
            scraped_gallery = scraped.get("gallery_images") or []
            media_urls.extend(scraped_gallery)
            media_urls = list(dict.fromkeys(media_urls))[:8]  # dedup, cap at 8

            content_json = json.dumps({
                "business_name": content.business_name,
                "industry_type": content.industry_type,
                "industry_archetype": content.industry_archetype,
                "brand_personality": content.brand_personality,
                "tagline": content.tagline,
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
                "media_urls": media_urls,             # ← IG/TikTok/website images
                # ── Scraped official website data (Stage 0.5) ───────────────
                "scraped": {
                    "hero_image_url": scraped.get("hero_image_url", ""),
                    "gallery_images": scraped_gallery[:6],
                    "about_text":     scraped.get("about_text", ""),
                    "tagline":        scraped.get("tagline", ""),
                    "menu_items":     scraped.get("menu_items") or [],
                },
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
                "hero_bg_gradient": design.hero_bg_gradient,
                "card_border_radius": design.card_border_radius,
                "font_weight_style": design.font_weight_style,
                "animation_style": design.animation_style,
                "section_divider": design.section_divider,
                "ui_instructions_for_developer": design.ui_instructions,
            }, ensure_ascii=False, indent=2)

            deepseek_json = json.dumps(deepseek_enrichment or {}, ensure_ascii=False, indent=2)
            mistral_json  = json.dumps(mistral_seo or {}, ensure_ascii=False, indent=2)
            cohere_json   = json.dumps(cohere_cro or {}, ensure_ascii=False, indent=2)
            grok_json     = json.dumps(grok_social or {}, ensure_ascii=False, indent=2)

            prompt_parts = [
                "Please build the complete, PREMIUM website. Use ALL data from ALL JSON blocks below.",
                "",
                f"═══ CONTENT JSON (Stage 1a) ═══\n{content_json}",
                "",
                f"═══ DESIGN SYSTEM JSON (Stage 1b) ═══\n{design_json}",
            ]

            if deepseek_enrichment:
                prompt_parts += [
                    "",
                    "═══ DEEPSEEK ENRICHMENT JSON (Stage 1c) ═══",
                    "MANDATORY: embed ALL faq items in accordion section [10], ALL usps in why-us [7],",
                    "ALL trust_signals in trust badges [4], buying_triggers as hero CTA sub-text,",
                    f"seo_description in <meta name=\"description\">:\n{deepseek_json}",
                ]

            if mistral_seo:
                prompt_parts += [
                    "",
                    "═══ MISTRAL SEO INTELLIGENCE JSON (Stage 1d) ═══",
                    "MANDATORY: use h1_tag as the page <h1>, h2_tags for section headings,",
                    "embed schema_json_ld verbatim in a <script type=\"application/ld+json\"> tag in <head>,",
                    f"meta_keywords in <meta name=\"keywords\">, rich_snippet_description in og:description:\n{mistral_json}",
                ]

            if cohere_cro:
                prompt_parts += [
                    "",
                    "═══ COHERE CRO PSYCHOLOGY JSON (Stage 1e) ═══",
                    "MANDATORY: use hero_cta_primary/secondary as the two hero button texts,",
                    "hero_urgency_line below the hero CTAs, objection_busters as an 'objections answered'",
                    "section before the contact strip, value_stack as a horizontal value propositions bar,",
                    f"whatsapp_opener as the pre-filled WhatsApp message (wa.me link with ?text= param):\n{cohere_json}",
                ]

            if grok_social:
                prompt_parts += [
                    "",
                    "═══ GROK SOCIAL PROOF JSON (Stage 1f) ═══",
                    "MANDATORY: use ALL 4 testimonials in a dedicated reviews/testimonials section with",
                    "stars, name, job_title and city. Use brand_story in the About Us section as the",
                    "opening paragraph. Use emotional_tagline as a secondary tagline beneath the hero headline.",
                    "Use social_proof_stat as a prominent badge/stat in the hero or trust bar.",
                    "Use trust_headline as the section <h2> for the testimonials section.",
                    f"Use about_hook as the first sentence of the about section:\n{grok_json}",
                ]

            prompt = "\n".join(prompt_parts)

            response = LLMRouterService().call_tracked(
                "build_site_html",
                prompt,
                system=_CLAUDE_BUILDER_SYSTEM_V2 if variant == 2 else _CLAUDE_BUILDER_SYSTEM,
                model="claude-sonnet-4-6",
                max_tokens=16000,
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
            # ── Post-process: fix truncated HTML and inject fade-up observer ──
            html = self._fix_html_output(html)
            return html
        except Exception:
            logger.exception("[Stage 2] Unhandled error")
            return None
