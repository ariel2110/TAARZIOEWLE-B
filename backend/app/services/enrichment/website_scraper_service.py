"""
Firecrawl-powered website scraper for business enrichment.

Extracts from the official business website:
  - Hero / gallery images
  - Tagline / headline text
  - About / description text
  - Menu items (name, description, price, image) — food businesses only

Falls back gracefully when:
  - FIRECRAWL_API_KEY is not set
  - The URL is not reachable
  - The page has no usable content
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Regex to detect a food/restaurant business
_FOOD_RE = re.compile(
    r'פיצ|גריל|שוורמ|פלאפל|המבורגר|מסעד|סושי|אוכל|קפה|מאפ|'
    r'restaurant|food|pizza|grill|burger|bakery|cafe|menu|תפריט',
    re.I,
)

# Regex to find a price in a line  (₪45 / 45 ₪ / 45 ש"ח)
_PRICE_RE = re.compile(r'₪\s*(\d+)|(\d+)\s*₪|(\d+)\s*ש["\u05f4]ח', re.I)

# Skip image URLs that look like icons / logos / sprites
_SKIP_IMG_RE = re.compile(r'logo|icon|favicon|avatar|sprite|pixel|placeholder|blank', re.I)

# Common "non-menu" section headings to ignore
_NON_MENU_HEADING_RE = re.compile(
    r'\babout\b|אודות|contact|צור קשר|footer|ראשי|home|gallery|'
    r'social|review|testimonial|blog|news|faq',
    re.I,
)


@dataclass
class WebsiteScraperResult:
    scraped_ok: bool = False
    hero_image_url: str = ""
    gallery_images: list[str] = field(default_factory=list)
    about_text: str = ""
    tagline: str = ""
    # [{cat, items:[{name, desc, price, image_url}]}]
    menu_items: list[dict] = field(default_factory=list)
    raw_text: str = ""


class WebsiteScraperService:
    """
    Stage 0.5 enrichment: scrape the business's own website.

    Usage:
        result = WebsiteScraperService().scrape(
            url="https://some-restaurant.co.il",
            category="מסעדה",
            business_types="שיפודייה גריל"
        )
        if result.scraped_ok:
            use result.hero_image_url, result.menu_items, ...
    """

    def __init__(self) -> None:
        from app.core.config import settings
        self.api_key: str = getattr(settings, "firecrawl_api_key", None) or ""

    # ── Public API ─────────────────────────────────────────────────────────────

    def scrape(
        self,
        url: str,
        category: str = "",
        business_types: str = "",
    ) -> WebsiteScraperResult:
        result = WebsiteScraperResult()
        if not self.api_key:
            logger.debug("[WebScraper] No FIRECRAWL_API_KEY — skipping")
            return result
        if not url:
            return result
        if not url.startswith("http"):
            url = "https://" + url

        try:
            from firecrawl import FirecrawlApp  # type: ignore[import]
        except ImportError:
            logger.warning("[WebScraper] firecrawl-py not installed — pip install firecrawl-py")
            return result

        try:
            app = FirecrawlApp(api_key=self.api_key)
            raw = app.scrape_url(
                url,
                params={
                    "formats": ["markdown", "links"],
                    "includeTags": ["img", "h1", "h2", "h3", "p", "meta", "table", "li"],
                    "excludeTags": ["script", "style", "iframe", "noscript"],
                    "timeout": 25000,
                },
            )
        except Exception as exc:
            logger.warning("[WebScraper] Firecrawl API error for %s: %s", url, exc)
            return result

        if not raw:
            return result

        result.scraped_ok = True
        markdown: str = raw.get("markdown") or ""
        links: list = raw.get("links") or []
        metadata: dict = raw.get("metadata") or {}
        result.raw_text = markdown

        # ── Images ─────────────────────────────────────────────────────────────
        images = self._extract_images(metadata, links, markdown)
        if images:
            result.hero_image_url = images[0]
            result.gallery_images = images

        # ── Text ───────────────────────────────────────────────────────────────
        result.tagline = self._extract_tagline(metadata, markdown)
        result.about_text = self._extract_about(markdown)

        # ── Menu (food businesses only) ────────────────────────────────────────
        combined = f"{category} {business_types} {url}"
        if _FOOD_RE.search(combined):
            result.menu_items = self._extract_menu(markdown)

        logger.info(
            "[WebScraper] OK url=%s | images=%d tagline=%r menu_cats=%d",
            url, len(images), result.tagline[:40] if result.tagline else "", len(result.menu_items),
        )
        return result

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _extract_images(self, metadata: dict, links: list, markdown: str) -> list[str]:
        seen: set[str] = set()
        images: list[str] = []

        def _add(url: str) -> None:
            if url and url.startswith("http") and url not in seen and not _SKIP_IMG_RE.search(url):
                seen.add(url)
                images.append(url)

        # 1. OG / Twitter card image (highest quality, usually hero)
        for key in ("og:image", "twitter:image", "ogImage"):
            og = metadata.get(key) or ""
            if og:
                _add(og)

        # 2. Links that end with an image extension
        for item in links:
            href = item if isinstance(item, str) else (item.get("href") or item.get("url") or "")
            if href and re.search(r'\.(jpe?g|png|webp)(\?|#|$)', href, re.I):
                _add(href)

        # 3. Inline markdown images  ![alt](url)
        for m in re.finditer(r'!\[.*?\]\((https?://[^)]+)\)', markdown):
            _add(m.group(1))

        return images[:8]

    def _extract_tagline(self, metadata: dict, markdown: str) -> str:
        # 1. OG title / description from metadata
        og_desc = metadata.get("og:description") or metadata.get("description") or ""
        if og_desc and 10 < len(og_desc) < 120:
            return og_desc.strip()

        # 2. First H1 in markdown that looks like a tagline
        for line in markdown.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# "):
                text = stripped[2:].strip()
                if 8 < len(text) < 100:
                    return text
        return ""

    def _extract_about(self, markdown: str) -> str:
        paragraphs: list[str] = []
        in_about = False
        for line in markdown.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            # Detect "about" heading
            if re.match(r'^#{1,3}\s+', stripped):
                heading = re.sub(r'^#{1,3}\s+', '', stripped)
                in_about = bool(re.search(r'about|אודות|עלינו|הסיפור|who we are', heading, re.I))
                continue
            # Collect long non-heading paragraphs
            if len(stripped) > 50 and not stripped.startswith("!"):
                if in_about or (not paragraphs and len(stripped) > 80):
                    paragraphs.append(stripped)
                    if len(paragraphs) >= 3:
                        break

        return " ".join(paragraphs)[:600] if paragraphs else ""

    def _extract_menu(self, markdown: str) -> list[dict]:
        """
        Parse markdown for a structured menu.
        Returns: [{cat: str, items: [{name, desc, price, image_url}]}]
        """
        categories: list[dict] = []
        current_cat: str | None = None
        current_items: list[dict] = []

        for line in markdown.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Section heading
            heading_m = re.match(r'^(#{1,3})\s+(.*)', stripped)
            if heading_m:
                # Save previous category
                if current_cat and current_items:
                    categories.append({"cat": current_cat, "items": current_items})
                    if len(categories) >= 7:
                        break
                title = heading_m.group(2).strip()
                if _NON_MENU_HEADING_RE.search(title):
                    current_cat = None
                    current_items = []
                else:
                    current_cat = title
                    current_items = []
                continue

            if current_cat is None:
                continue

            # Try to extract a menu item with price
            price_m = _PRICE_RE.search(stripped)
            if price_m:
                price_val = int(
                    price_m.group(1) or price_m.group(2) or price_m.group(3) or 0
                )
                if not (3 < price_val < 2000):
                    continue
                name_part = _PRICE_RE.sub("", stripped).strip().strip("|–—-").strip()
                # Split name | description
                parts = re.split(r'\||\u2014|\u2013|—', name_part, maxsplit=1)
                name = parts[0].strip()[:80]
                desc = parts[1].strip()[:120] if len(parts) > 1 else ""
                if name:
                    current_items.append({
                        "name": name,
                        "desc": desc,
                        "price": price_val,
                        "image_url": "",
                    })
            # Bullet point without price (add as name-only if plausible)
            elif re.match(r'^[-•*]\s+', stripped):
                text = re.sub(r'^[-•*]\s+', '', stripped).strip()
                if 3 < len(text) < 80 and current_items is not None:
                    current_items.append({"name": text, "desc": "", "price": 0, "image_url": ""})

        # Save last category
        if current_cat and current_items:
            categories.append({"cat": current_cat, "items": current_items})

        return categories[:7]
