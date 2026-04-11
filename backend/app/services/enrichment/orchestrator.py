"""
Business cross-reference & enrichment orchestrator.
Combines Places data + social data + LLM to produce a full profile
ready for site generation.
"""
from __future__ import annotations

import logging
from app.services.enrichment.places_service import PlacesService
from app.services.enrichment.social_service import SocialEnrichmentService

logger = logging.getLogger(__name__)

places_svc  = PlacesService()
social_svc  = SocialEnrichmentService()


class EnrichmentOrchestrator:

    def search_and_enrich(
        self,
        city: str,
        category: str = "",
        limit: int = 50,
        include_social: bool = True,
    ) -> list[dict]:
        """
        Main entry point: fetch businesses from Places, enrich each
        with social media links and a cross-reference confidence score.
        """
        raw_businesses = places_svc.search_businesses(city, category, limit)
        results = []
        for biz in raw_businesses:
            enriched = dict(biz)
            if include_social:
                social = social_svc.find_social(
                    business_name=biz.get("name", ""),
                    website=biz.get("website", ""),
                    city=city,
                )
                enriched.update({
                    "facebook_url":    social.get("facebook_url", ""),
                    "instagram_url":   social.get("instagram_url", ""),
                    "social_confidence": social.get("confidence", "low"),
                    "social_sources":  social.get("sources", []),
                })
            else:
                enriched.update({"facebook_url": "", "instagram_url": "", "social_confidence": "unknown", "social_sources": []})

            enriched["completeness_score"] = self._completeness(enriched)
            results.append(enriched)

        # Sort by completeness (most data-rich first)
        results.sort(key=lambda x: x["completeness_score"], reverse=True)
        return results

    def enrich_single(self, place_id: str, include_social: bool = True) -> dict | None:
        detail = places_svc.enrich_single(place_id)
        if not detail:
            return None
        if include_social:
            social = social_svc.find_social(
                business_name=detail.get("name", ""),
                website=detail.get("website", ""),
            )
            detail.update({
                "facebook_url":    social.get("facebook_url", ""),
                "instagram_url":   social.get("instagram_url", ""),
                "social_confidence": social.get("confidence", "low"),
            })
        detail["completeness_score"] = self._completeness(detail)
        return detail

    # ------------------------------------------------------------------

    def _completeness(self, b: dict) -> int:
        """Score 0–100 based on available data fields."""
        score = 0
        if b.get("name"):           score += 15
        if b.get("phone"):          score += 15
        if b.get("address"):        score += 10
        if b.get("website"):        score += 20
        if b.get("facebook_url"):   score += 15
        if b.get("instagram_url"):  score += 10
        if b.get("rating"):         score += 5
        if b.get("reviews_count", 0) > 10: score += 5
        if b.get("opening_hours"):  score += 5
        return score
