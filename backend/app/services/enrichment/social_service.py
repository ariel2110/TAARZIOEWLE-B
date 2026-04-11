"""
Social media enrichment service.
Searches for Facebook pages and Instagram profiles for a given business.
Uses Facebook Graph API when token is available, otherwise performs
a URL-pattern heuristic and cross-reference search.
"""
from __future__ import annotations

import re
import logging
import httpx
from urllib.parse import quote_plus
from app.core.config import settings

logger = logging.getLogger(__name__)


class SocialEnrichmentService:

    def find_social(self, business_name: str, website: str = "", city: str = "") -> dict:
        """
        Attempt to find Facebook and Instagram handles for a business.
        Returns dict with keys: facebook_url, instagram_url, facebook_page_id, confidence
        """
        result: dict = {
            "facebook_url": "",
            "instagram_url": "",
            "facebook_page_id": "",
            "confidence": "low",
            "sources": [],
        }

        # 1. Try to extract social links from the business website
        if website:
            self._scrape_website_social(website, result)

        # 2. Try name-based URL guesses
        slug = self._to_slug(business_name)
        if not result["facebook_url"]:
            guessed_fb = f"https://www.facebook.com/{slug}"
            if self._url_exists(guessed_fb):
                result["facebook_url"] = guessed_fb
                result["sources"].append("url_guess")
                result["confidence"] = "medium"

        if not result["instagram_url"]:
            guessed_ig = f"https://www.instagram.com/{slug}"
            if self._url_exists(guessed_ig):
                result["instagram_url"] = guessed_ig
                result["sources"].append("url_guess")
                result["confidence"] = "medium"

        # 3. Facebook Graph API search (if token available)
        fb_token = getattr(settings, "facebook_access_token", None)
        if fb_token and not result["facebook_url"]:
            self._graph_search(business_name, city, result, fb_token)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scrape_website_social(self, website: str, result: dict) -> None:
        if not website.startswith("http"):
            website = "https://" + website
        try:
            resp = httpx.get(website, timeout=6, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text
            # Facebook
            fb_match = re.search(r'https?://(?:www\.)?facebook\.com/([A-Za-z0-9_.]+)', html)
            if fb_match:
                result["facebook_url"] = fb_match.group(0).split("?")[0]
                result["sources"].append("website_scrape")
                result["confidence"] = "high"
            # Instagram
            ig_match = re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)', html)
            if ig_match:
                result["instagram_url"] = ig_match.group(0).split("?")[0]
                result["sources"].append("website_scrape")
                result["confidence"] = "high"
        except Exception as e:
            logger.debug("Website scrape failed for %s: %s", website, e)

    def _to_slug(self, name: str) -> str:
        """Convert business name to a URL-friendly slug."""
        name = name.lower()
        # Remove common Hebrew/English stop words
        for word in ["מסעדת", "חנות", "קפה", "בית", "ספר", "סטודיו", "מכון", "מאפיית"]:
            name = name.replace(word, "")
        # Keep only alphanumeric + spaces
        name = re.sub(r"[^\w\s]", "", name, flags=re.UNICODE)
        name = name.strip().replace(" ", "")
        return name[:30] if name else "business"

    def _url_exists(self, url: str) -> bool:
        try:
            resp = httpx.head(url, timeout=4, follow_redirects=True)
            # Facebook/Instagram return 200 for existing pages, redirect for non-existing
            return resp.status_code in (200, 301, 302)
        except Exception:
            return False

    def _graph_search(self, name: str, city: str, result: dict, token: str) -> None:
        query = f"{name} {city}".strip()
        try:
            resp = httpx.get(
                "https://graph.facebook.com/v19.0/search",
                params={"q": query, "type": "page", "access_token": token, "fields": "id,name,link"},
                timeout=8,
            )
            data = resp.json()
            pages = data.get("data", [])
            if pages:
                page = pages[0]
                result["facebook_url"] = page.get("link", f"https://facebook.com/{page.get('id', '')}")
                result["facebook_page_id"] = page.get("id", "")
                result["sources"].append("graph_api")
                result["confidence"] = "high"
        except Exception as e:
            logger.debug("Graph API search failed: %s", e)
