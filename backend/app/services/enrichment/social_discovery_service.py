"""Social & Web Intelligence Discovery Service
===============================================
Stage 0 of the AutoSite pipeline — runs BEFORE content generation.

Discovers and cross-validates digital assets for a business:
  • Facebook page
  • Instagram profile
  • TikTok handle
  • Easy (איזי) directory listing
  • b144 directory listing
  • Legacy website (old, non-mobile-friendly site)

Validation flow:
  1. Serper API: 6 targeted search queries (limit=3 results each → minimal credits)
  2. Website scrape: extract social links from existing site
  3. Gemini Flash: cross-check phone/address/name → Confidence Score (0–100)
  4. Classify digital gap: 'super_hot' (strong social + no/old site) | 'hot' | None

Returns a SocialProfile dataclass. Designed to fail gracefully — any exception
produces an empty (but valid) SocialProfile so the pipeline is never blocked.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_SERPER_URL = "https://google.serper.dev/search"
_TIMEOUT = 6  # seconds per HTTP call


# ── Data contract ──────────────────────────────────────────────────────────────

@dataclass
class SocialProfile:
    facebook_url: str = ""
    instagram_url: str = ""
    tiktok_url: str = ""
    easy_url: str = ""
    b144_url: str = ""
    legacy_site_url: str = ""
    social_verified: bool = False
    social_confidence: int = 0          # 0–100
    digital_gap_label: str = ""         # 'super_hot' | 'hot' | ''
    easy_hours: list[str] = field(default_factory=list)
    easy_services: list[str] = field(default_factory=list)
    legacy_text_snippets: list[str] = field(default_factory=list)
    tone_hint: str = ""                 # 'young_creative' | 'formal' | 'casual' — inferred from social
    sources: list[str] = field(default_factory=list)
    # Apify-fetched social media content
    instagram_media_urls: list[str] = field(default_factory=list)   # up to 3 recent IG images
    tiktok_media_urls: list[str] = field(default_factory=list)      # up to 3 recent TikTok covers
    # Serper /places structured data
    places_phone: str = ""
    places_address: str = ""
    places_rating: float = 0.0
    places_rating_count: int = 0
    places_category: str = ""
    places_price_level: str = ""
    places_cid: str = ""


# ── Main service class ─────────────────────────────────────────────────────────

class SocialDiscoveryService:
    """
    Usage:
        profile = SocialDiscoveryService().discover(
            business_name="100% POWER",
            city="תל אביב",
            phone="0501234567",
            website="https://oldsite.co.il",
        )
    """

    def discover(
        self,
        business_name: str,
        city: str = "",
        phone: str = "",
        website: str = "",
        category: str = "",
    ) -> SocialProfile:
        profile = SocialProfile()
        try:
            # 1. Scrape existing website for social links
            if website:
                self._scrape_website(website, profile)

            # 2. Serper searches (only if API key is configured)
            if settings.serper_api_key:
                self._serper_discover(business_name, city, category, profile)
            else:
                logger.info("[SocialDiscovery] No SERPER_API_KEY — skipping search queries")
                # Fallback: URL heuristic
                self._url_heuristic(business_name, profile)

            # 3. Scrape legacy site for text snippets
            if profile.legacy_site_url and not profile.legacy_text_snippets:
                self._extract_legacy_text(profile.legacy_site_url, profile)

            # 4. Cross-validate with Gemini (if we found something)
            if any([profile.facebook_url, profile.instagram_url, profile.tiktok_url,
                    profile.easy_url, profile.legacy_site_url]) and phone:
                self._validate_with_gemini(business_name, city, phone, profile)

            # 5. Classify digital gap
            self._classify_gap(profile)

            # 6. Infer tone from social presence
            self._infer_tone(profile)

            # 7. Apify: fetch last 3 media items from verified IG/TikTok profiles
            if settings.apify_api_token and (profile.instagram_url or profile.tiktok_url):
                self._fetch_apify_media(profile)

        except Exception:
            logger.exception("[SocialDiscovery] Unhandled error for %r", business_name)

        logger.info(
            "[SocialDiscovery] %r → fb=%s ig=%s tk=%s easy=%s legacy=%s conf=%d gap=%r",
            business_name,
            bool(profile.facebook_url), bool(profile.instagram_url),
            bool(profile.tiktok_url), bool(profile.easy_url),
            bool(profile.legacy_site_url),
            profile.social_confidence, profile.digital_gap_label,
        )
        return profile

    # ── Serper multi-query discovery ──────────────────────────────────────────

    def _serper_discover(self, name: str, city: str, category: str, profile: SocialProfile) -> None:
        queries = [
            (f'site:facebook.com "{name}" {city}', "facebook"),
            (f'site:instagram.com "{name}"', "instagram"),
            (f'site:tiktok.com "{name}"', "tiktok"),
            (f'site:easy.co.il "{name}" {city}', "easy"),
            (f'site:b144.co.il "{name}" {city}', "b144"),
            # Legacy site: find old web presence that isn't a social network or directory
            (f'"{name}" {city} {category} -site:facebook.com -site:instagram.com -site:easy.co.il -site:b144.co.il -site:wix.com -site:google.com', "legacy"),
        ]

        headers = {
            "X-API-KEY": settings.serper_api_key,
            "Content-Type": "application/json",
        }

        for query, kind in queries:
            try:
                resp = httpx.post(
                    _SERPER_URL,
                    headers=headers,
                    json={"q": query, "num": 3, "gl": "il", "hl": "iw"},
                    timeout=_TIMEOUT,
                )
                data = resp.json()
                results = data.get("organic", [])
                if not results:
                    continue

                top_url = results[0].get("link", "")
                snippet = results[0].get("snippet", "")

                if kind == "facebook" and not profile.facebook_url:
                    url = self._extract_clean_url(top_url, "facebook.com")
                    if url:
                        profile.facebook_url = url
                        profile.sources.append("serper_facebook")

                elif kind == "instagram" and not profile.instagram_url:
                    url = self._extract_clean_url(top_url, "instagram.com")
                    if url:
                        profile.instagram_url = url
                        profile.sources.append("serper_instagram")

                elif kind == "tiktok" and not profile.tiktok_url:
                    url = self._extract_clean_url(top_url, "tiktok.com")
                    if url:
                        profile.tiktok_url = url
                        profile.sources.append("serper_tiktok")

                elif kind == "easy" and not profile.easy_url:
                    url = self._extract_clean_url(top_url, "easy.co.il")
                    if url:
                        profile.easy_url = url
                        profile.sources.append("serper_easy")
                        # Extract hours/services from snippet
                        if snippet:
                            self._parse_easy_snippet(snippet, profile)

                elif kind == "b144" and not profile.b144_url:
                    url = self._extract_clean_url(top_url, "b144.co.il")
                    if url:
                        profile.b144_url = url
                        profile.sources.append("serper_b144")

                elif kind == "legacy" and not profile.legacy_site_url:
                    # Reject social/directory sites and SaaS builders
                    blacklist = [
                        "facebook", "instagram", "tiktok", "youtube", "google",
                        "easy.co.il", "b144", "wix.com", "wordpress.com",
                        "weebly", "site123", "websitebuilder",
                    ]
                    if top_url and not any(b in top_url for b in blacklist):
                        profile.legacy_site_url = top_url
                        profile.sources.append("serper_legacy")

            except Exception as e:
                logger.debug("[SocialDiscovery] Serper query %r failed: %s", kind, e)

    # ── Website scraping for social links ─────────────────────────────────────

    def _scrape_website(self, website: str, profile: SocialProfile) -> None:
        if not website.startswith("http"):
            website = "https://" + website
        try:
            resp = httpx.get(website, timeout=_TIMEOUT, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text

            if not profile.facebook_url:
                m = re.search(r'https?://(?:www\.)?facebook\.com/([A-Za-z0-9_.]+)', html)
                if m:
                    profile.facebook_url = m.group(0).split("?")[0]
                    profile.sources.append("website_scrape")

            if not profile.instagram_url:
                m = re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)', html)
                if m:
                    profile.instagram_url = m.group(0).split("?")[0]
                    profile.sources.append("website_scrape")

            if not profile.tiktok_url:
                m = re.search(r'https?://(?:www\.)?tiktok\.com/@([A-Za-z0-9_.]+)', html)
                if m:
                    profile.tiktok_url = m.group(0).split("?")[0]
                    profile.sources.append("website_scrape")

        except Exception as e:
            logger.debug("[SocialDiscovery] Website scrape failed for %s: %s", website, e)

    # ── URL heuristic fallback (no API key) ───────────────────────────────────

    def _url_heuristic(self, business_name: str, profile: SocialProfile) -> None:
        slug = self._to_slug(business_name)
        for platform, url_template in [
            ("facebook", f"https://www.facebook.com/{slug}"),
            ("instagram", f"https://www.instagram.com/{slug}"),
        ]:
            attr = f"{platform}_url"
            if not getattr(profile, attr):
                try:
                    r = httpx.head(url_template, timeout=4, follow_redirects=True)
                    if r.status_code < 400:
                        setattr(profile, attr, url_template)
                        profile.sources.append(f"url_heuristic_{platform}")
                except Exception:
                    pass

    # ── Legacy site: extract useful text ─────────────────────────────────────

    def _extract_legacy_text(self, url: str, profile: SocialProfile) -> None:
        try:
            resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            # strip tags, keep meaningful text
            text = re.sub(r'<[^>]+>', ' ', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()
            # Take up to 3 snippets of ~150 chars from distinct areas
            chunks = [text[i:i+150].strip() for i in range(0, min(len(text), 900), 300) if text[i:i+150].strip()]
            profile.legacy_text_snippets = chunks[:3]
        except Exception as e:
            logger.debug("[SocialDiscovery] Legacy site text extraction failed: %s", e)

    # ── Easy snippet parsing ──────────────────────────────────────────────────

    def _parse_easy_snippet(self, snippet: str, profile: SocialProfile) -> None:
        # Hours: look for patterns like "א'-ו' 08:00-18:00" or "09:00-19:00"
        hours = re.findall(r"(?:[א-ת]'[–-][א-ת]'|[א-ת]')[^\s]*\s*\d{1,2}:\d{2}[–-]\d{1,2}:\d{2}", snippet)
        if hours:
            profile.easy_hours = hours[:5]
        # Services: short comma-separated items before the hours
        services_part = snippet.split(",")
        services = [s.strip() for s in services_part if 2 < len(s.strip()) < 40]
        if services:
            profile.easy_services = services[:5]

    # ── Gemini Flash cross-validation ────────────────────────────────────────

    def _validate_with_gemini(
        self, name: str, city: str, phone: str, profile: SocialProfile
    ) -> None:
        try:
            from app.services.llm.router_service import LLMRouterService
            found_assets = {
                "facebook": profile.facebook_url,
                "instagram": profile.instagram_url,
                "tiktok": profile.tiktok_url,
                "easy": profile.easy_url,
                "b144": profile.b144_url,
                "legacy_site": profile.legacy_site_url,
            }
            prompt = (
                f"Business verification task — strict detective cross-check.\n"
                f"KNOWN GROUND TRUTH:\n"
                f"  Name: {name}\n"
                f"  City: {city}\n"
                f"  Phone: {phone}\n\n"
                f"FOUND DIGITAL ASSETS:\n"
                f"{json.dumps(found_assets, ensure_ascii=False, indent=2)}\n\n"
                "For each found asset, assess if it likely belongs to THIS business "
                "(same name/city/phone/category match). "
                "Output ONLY strict JSON:\n"
                "{\n"
                '  "confidence_score": <0-100 integer>,\n'
                '  "verified_assets": ["facebook", "instagram", ...],\n'  
                '  "rejected_assets": ["tiktok", ...],\n'
                '  "reason": "<1 sentence Hebrew explanation>"\n'
                "}"
            )
            resp = LLMRouterService().call_tracked(
                "analyze_business_data",
                prompt,
                model="gemini-2.5-flash",
                max_tokens=300,
                json_mode=True,
                stage="social_discovery",
            )
            if not resp:
                return
            data = json.loads(resp) if isinstance(resp, str) else resp
            score = int(data.get("confidence_score", 0))
            profile.social_confidence = min(100, max(0, score))
            _verified = set(data.get("verified_assets", []))
            rejected = set(data.get("rejected_assets", []))

            if score >= 85:
                profile.social_verified = True

            # Clear rejected assets
            for asset in rejected:
                attr = f"{asset}_url"
                if hasattr(profile, attr):
                    setattr(profile, attr, "")
                    logger.info("[SocialDiscovery] Rejected %s (low confidence)", asset)

        except Exception as e:
            logger.debug("[SocialDiscovery] Gemini validation failed: %s", e)
            # If Gemini fails, use a generous default so we don't lose good data
            profile.social_confidence = 60

    # ── Digital gap classification ────────────────────────────────────────────

    def _classify_gap(self, profile: SocialProfile) -> None:
        has_social = bool(profile.facebook_url or profile.instagram_url or profile.tiktok_url)
        has_old_site = bool(profile.legacy_site_url)
        no_current_site = not profile.legacy_site_url  # True if totally missing web presence

        if has_social and has_old_site:
            # Strong social + outdated site = goldmine
            profile.digital_gap_label = "super_hot"
        elif has_social and no_current_site:
            # Strong social + zero web = hot
            profile.digital_gap_label = "hot"
        elif has_old_site:
            profile.digital_gap_label = "hot"
        else:
            profile.digital_gap_label = ""

    # ── Tone inference from social presence ──────────────────────────────────

    def _infer_tone(self, profile: SocialProfile) -> None:
        """Infer content tone from which platforms are active."""
        if profile.tiktok_url:
            profile.tone_hint = "young_creative"
        elif profile.instagram_url and not profile.facebook_url:
            profile.tone_hint = "visual_casual"
        elif profile.facebook_url and profile.easy_url:
            profile.tone_hint = "formal_local"
        elif profile.facebook_url:
            profile.tone_hint = "casual"
        else:
            profile.tone_hint = "neutral"

    # ── Apify: social media content fetching ─────────────────────────────────

    def _fetch_apify_media(self, profile: SocialProfile) -> None:
        """Fetch last 3 media URLs from verified Instagram / TikTok profiles via Apify.
        Runs only when APIFY_API_TOKEN is set. Fails silently on any error.
        """
        try:
            from apify_client import ApifyClient
            client = ApifyClient(settings.apify_api_token)
        except ImportError:
            logger.debug("[SocialDiscovery] apify-client not installed — skipping media fetch")
            return

        # ── Instagram ─────────────────────────────────────────────────────────
        if profile.instagram_url:
            try:
                username = profile.instagram_url.rstrip("/").split("/")[-1].lstrip("@").split("?")[0]
                if username:
                    run = client.actor("apify/instagram-scraper").call(
                        run_input={
                            "usernames": [username],
                            "resultsType": "posts",
                            "resultsLimit": 3,
                        },
                        timeout_secs=45,
                        memory_mbytes=256,
                    )
                    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                    media = [
                        item.get("displayUrl") or item.get("videoUrl")
                        for item in items
                        if item.get("displayUrl") or item.get("videoUrl")
                    ]
                    profile.instagram_media_urls = [u for u in media if u][:3]
                    logger.info(
                        "[SocialDiscovery] Apify IG: fetched %d media for @%s",
                        len(profile.instagram_media_urls), username,
                    )
            except Exception as e:
                logger.debug("[SocialDiscovery] Apify Instagram fetch failed: %s", e)

        # ── TikTok ────────────────────────────────────────────────────────────
        if profile.tiktok_url:
            try:
                username = profile.tiktok_url.rstrip("/").split("/")[-1].lstrip("@").split("?")[0]
                if username:
                    run = client.actor("clockworks/free-tiktok-scraper").call(
                        run_input={
                            "profiles": [f"@{username}"],
                            "resultsPerPage": 3,
                            "shouldDownloadVideos": False,
                            "shouldDownloadCovers": True,
                        },
                        timeout_secs=60,
                        memory_mbytes=256,
                    )
                    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                    media = [
                        (item.get("videoMeta") or {}).get("coverUrl")
                        or item.get("webVideoUrl")
                        for item in items
                    ]
                    profile.tiktok_media_urls = [u for u in media if u][:3]
                    logger.info(
                        "[SocialDiscovery] Apify TikTok: fetched %d covers for @%s",
                        len(profile.tiktok_media_urls), username,
                    )
            except Exception as e:
                logger.debug("[SocialDiscovery] Apify TikTok fetch failed: %s", e)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _extract_clean_url(self, url: str, domain: str) -> str:
        """Return the URL only if it contains the expected domain, stripped of query params."""
        if not url or domain not in url:
            return ""
        return url.split("?")[0].rstrip("/")

    def _to_slug(self, name: str) -> str:
        name = name.lower()
        for word in ["מסעדת", "חנות", "קפה", "בית", "ספר", "סטודיו", "מכון", "מאפיית"]:
            name = name.replace(word, "")
        name = re.sub(r"[^\w\s]", "", name, flags=re.UNICODE)
        return name.strip().replace(" ", "")[:30] or "business"
