"""
Zero-Hallucination Cross-Reference Engine
==========================================

Validates that social/web agent data (Facebook, Instagram, Serper) genuinely
belongs to the same business as the Google Places anchor, before expensive
content-generation agents (Claude) are triggered.

Scoring Matrix (0-100):
  +50  Phone normalization match
  +30  Domain/URL cross-check
  +20  Geofencing (<15 km)
  LLM  Gemini semantic name match (boolean gate — can veto)

Thresholds:
  >85  → Verified    (proceed to site generation)
  50–85 → Manual Review (halt automation, alert admin)
  <50  → Mismatch   (discard social data, use Places only)
"""
from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Literal

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Types ─────────────────────────────────────────────────────────────────────

CRStatus = Literal['verified', 'manual_review', 'mismatch', 'pending']


@dataclass
class AgentData:
    """Normalised data from any agent (anchor or challenger)."""
    agent: str                       # 'google_places' | 'facebook' | 'instagram' | 'serper'
    name: str | None = None
    phone: str | None = None
    website: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    extra_text: str | None = None    # bio, about section, snippet etc.


@dataclass
class ScoreBreakdown:
    phone_score: int = 0             # 0 or 50
    domain_score: int = 0            # 0 or 30
    geo_score: int = 0               # 0 or 20
    geo_failed: bool = False         # True = geofence violated (-100)
    name_match: bool | None = None   # LLM result (None = not run)
    name_vetoed: bool = False        # LLM returned hard mismatch


@dataclass
class AgentMatchResult:
    agent: str
    passed: bool
    score: int
    breakdown: ScoreBreakdown


@dataclass
class CrossReferenceResult:
    score: int                                          # 0-100 clamped
    status: CRStatus
    breakdown: ScoreBreakdown
    agent_results: list[AgentMatchResult] = field(default_factory=list)
    agent_statuses: dict[str, bool] = field(default_factory=dict)  # for dashboard icons


# ── Helpers ───────────────────────────────────────────────────────────────────

_GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'


def _normalize_phone(raw: str | None) -> str:
    """Strip all non-digit chars; convert +972 prefix to 0."""
    if not raw:
        return ''
    digits = re.sub(r'\D', '', raw)
    # +972 XX → 0XX (Israel standard)
    if digits.startswith('972') and len(digits) >= 10:
        digits = '0' + digits[3:]
    # 00972 XX → 0XX
    if digits.startswith('00972') and len(digits) >= 11:
        digits = '0' + digits[5:]
    return digits


def _extract_domain(url: str | None) -> str:
    """Return the registrable domain (e.g. 'example.co.il') from a URL."""
    if not url:
        return ''
    url = url.lower().strip()
    # strip scheme
    url = re.sub(r'^https?://', '', url)
    # strip path
    domain = url.split('/')[0].split('?')[0]
    # strip www.
    domain = re.sub(r'^www\.', '', domain)
    return domain


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two GPS points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _geocode_address(address: str) -> tuple[float, float] | None:
    """Geocode a free-text address via Google Maps API. Returns (lat, lng) or None."""
    key = settings.google_places_api_key
    if not key or not address:
        return None
    try:
        r = httpx.get(
            _GEOCODE_URL,
            params={'address': address, 'key': key, 'language': 'he', 'region': 'il'},
            timeout=6,
        )
        data = r.json()
        if data.get('status') == 'OK' and data.get('results'):
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except Exception as exc:
        logger.debug('Geocode failed for %r: %s', address[:40], type(exc).__name__)
    return None


def _gemini_name_match(name_anchor: str, name_challenger: str) -> bool | None:
    """
    Ask Gemini whether two business names refer to the SAME business.
    Returns True (match), False (mismatch), or None (API unavailable).
    The model must reply with a single JSON: {"match": true/false}.
    """
    key = settings.gemini_api_key
    if not key or not name_anchor or not name_challenger:
        return None

    prompt = (
        'You are a business entity resolver. Decide whether the following two names '
        'refer to the SAME physical business. Consider transliterations, abbreviations, '
        'and Hebrew/English equivalents.\n\n'
        f'Name A: "{name_anchor}"\n'
        f'Name B: "{name_challenger}"\n\n'
        'Respond with JSON only — exactly: {"match": true} or {"match": false}'
    )

    try:
        r = httpx.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}',
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'temperature': 0, 'maxOutputTokens': 32},
            },
            timeout=10,
        )
        text = (
            r.json()
            .get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', '')
        ).strip()
        # Extract JSON even if wrapped in markdown
        match = re.search(r'\{.*\}', text)
        if match:
            parsed = json.loads(match.group())
            return bool(parsed.get('match'))
    except Exception as exc:
        logger.warning('Gemini name match failed: %s', type(exc).__name__)
    return None


# ── Core Engine ───────────────────────────────────────────────────────────────

class CrossReferenceValidator:
    """
    Validates a set of challenger agents against a Google Places anchor.

    Usage:
        validator = CrossReferenceValidator()
        anchor = AgentData(agent='google_places', name='מוסך רונן',
                           phone='054-1234567', website='ronenmotors.co.il',
                           lat=32.08, lng=34.78)
        challengers = [
            AgentData(agent='facebook', name='Ronen Motors TLV',
                      website='https://ronenmotors.co.il'),
        ]
        result = validator.validate(anchor, challengers)
    """

    def validate(
        self,
        anchor: AgentData,
        challengers: list[AgentData],
    ) -> CrossReferenceResult:
        """Run full validation pipeline; return aggregated CrossReferenceResult."""
        if not challengers:
            return CrossReferenceResult(
                score=0,
                status='pending',
                breakdown=ScoreBreakdown(),
                agent_statuses={'google_places': True},
            )

        agent_results: list[AgentMatchResult] = []
        for challenger in challengers:
            result = self.calculate_entity_match_score(anchor, challenger)
            agent_results.append(result)

        # Aggregate: use the highest-scoring challenger as the primary score
        best = max(agent_results, key=lambda r: r.score)
        score = best.score
        status = self._classify(score)

        agent_statuses = {'google_places': True}
        for r in agent_results:
            agent_statuses[r.agent] = r.passed

        return CrossReferenceResult(
            score=score,
            status=status,
            breakdown=best.breakdown,
            agent_results=agent_results,
            agent_statuses=agent_statuses,
        )

    def calculate_entity_match_score(
        self,
        anchor: AgentData,
        challenger: AgentData,
    ) -> AgentMatchResult:
        """
        Score how likely a challenger agent found the same business as the anchor.

        Returns AgentMatchResult with score (0-100) and breakdown.
        """
        bd = ScoreBreakdown()
        raw_score = 0

        # ── 1. Phone normalization (+50) ──────────────────────────────────────
        anchor_phone = _normalize_phone(anchor.phone)
        chall_phone = _normalize_phone(challenger.phone)
        if anchor_phone and chall_phone:
            if anchor_phone == chall_phone:
                bd.phone_score = 50
                raw_score += 50
                logger.debug('[CrossRef] Phone MATCH for %s', challenger.agent)
            else:
                logger.debug('[CrossRef] Phone MISMATCH anchor=%s chall=%s agent=%s',
                             anchor_phone, chall_phone, challenger.agent)
        # If one side has no phone: no deduction (data might just be missing)

        # ── 2. Domain / URL cross-check (+30) ────────────────────────────────
        anchor_domain = _extract_domain(anchor.website)
        chall_domain = _extract_domain(challenger.website)
        # Also scan extra_text (bio, about) for the domain
        extra = (challenger.extra_text or '').lower()
        if anchor_domain:
            domain_in_extra = anchor_domain in extra
            domain_match = bool(chall_domain and chall_domain == anchor_domain)
            if domain_match or domain_in_extra:
                bd.domain_score = 30
                raw_score += 30
                logger.debug('[CrossRef] Domain MATCH for %s', challenger.agent)

        # ── 3. Strict Geofencing (+20 or instant fail) ───────────────────────
        anchor_has_gps = anchor.lat is not None and anchor.lng is not None
        if anchor_has_gps:
            chall_lat: float | None = challenger.lat
            chall_lng: float | None = challenger.lng
            # If challenger has no coords but has an address, try to geocode
            if chall_lat is None and challenger.address:
                coords = _geocode_address(challenger.address)
                if coords:
                    chall_lat, chall_lng = coords
            if chall_lat is not None and chall_lng is not None:
                dist_km = _haversine_km(anchor.lat, anchor.lng, chall_lat, chall_lng)
                if dist_km > 15:
                    # Instant fail — completely different location
                    bd.geo_failed = True
                    raw_score = -100
                    logger.warning(
                        '[CrossRef] Geofence FAIL %.1f km for %s', dist_km, challenger.agent
                    )
                else:
                    bd.geo_score = 20
                    raw_score += 20
                    logger.debug('[CrossRef] Geofence OK %.1f km for %s', dist_km, challenger.agent)

        # ── 4. LLM Semantic Name Match (boolean gate) ────────────────────────
        if anchor.name and challenger.name:
            bd.name_match = _gemini_name_match(anchor.name, challenger.name)
            if bd.name_match is False:
                # Hard mismatch — names are definitely different businesses
                bd.name_vetoed = True
                raw_score = max(raw_score - 40, 0)
                logger.warning(
                    '[CrossRef] LLM name VETO anchor=%r chall=%r agent=%s',
                    anchor.name, challenger.name, challenger.agent,
                )
            elif bd.name_match is True:
                # Confidence boost only if score is borderline
                if raw_score > 0 and raw_score < 50:
                    raw_score += 10  # small nudge for confirmed name match

        # Clamp to 0-100
        final_score = max(0, min(100, raw_score))
        passed = final_score >= 50

        return AgentMatchResult(
            agent=challenger.agent,
            passed=passed,
            score=final_score,
            breakdown=bd,
        )

    @staticmethod
    def _classify(score: int) -> CRStatus:
        if score > 85:
            return 'verified'
        if score >= 50:
            return 'manual_review'
        return 'mismatch'

    @staticmethod
    def build_anchor(
        *,
        name: str | None,
        phone: str | None,
        website: str | None,
        address: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> AgentData:
        return AgentData(
            agent='google_places',
            name=name,
            phone=phone,
            website=website,
            address=address,
            lat=lat,
            lng=lng,
        )

    @staticmethod
    def build_social_challengers(
        *,
        facebook_url: str | None = None,
        instagram_url: str | None = None,
        serper_name: str | None = None,
        serper_url: str | None = None,
        serper_snippet: str | None = None,
        anchor_name: str | None = None,
    ) -> list[AgentData]:
        """
        Build challenger AgentData objects from what the social discovery pipeline
        already found. We don't have phone/address from social at this stage —
        validation relies primarily on domain and LLM name match.
        """
        challengers: list[AgentData] = []

        if facebook_url:
            challengers.append(AgentData(
                agent='facebook',
                name=anchor_name,   # will be refined if FB profile data is available
                website=facebook_url,
                extra_text=facebook_url,
            ))

        if instagram_url:
            challengers.append(AgentData(
                agent='instagram',
                name=anchor_name,
                website=instagram_url,
                extra_text=instagram_url,
            ))

        if serper_name or serper_url:
            challengers.append(AgentData(
                agent='serper',
                name=serper_name,
                website=serper_url,
                extra_text=serper_snippet,
            ))

        return challengers


# Singleton
validator = CrossReferenceValidator()
