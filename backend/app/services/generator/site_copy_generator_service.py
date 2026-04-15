from __future__ import annotations
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SiteCopyResult:
    hero_title: str
    about_text: str
    services_list: list[str]
    tagline: str


class SiteCopyGeneratorService:
    """Generates Hebrew marketing copy for a business landing page using the LLM.

    Falls back to rule-based templates when no LLM key is configured or the call fails.
    """

    def generate(self, *, name: str, city: str | None, category: str | None) -> SiteCopyResult:
        from app.services.llm.router_service import LLMRouterService

        llm = LLMRouterService()
        prompt = self._build_prompt(name=name, city=city, category=category)
        raw = llm.call_tracked("generate_site_copy", prompt, json_mode=True, stage="site_copy_gen")
        if raw:
            parsed = self._parse_response(raw)
            if parsed:
                return parsed

        # Graceful fallback — rule-based
        return self._fallback(name=name, city=city, category=category)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, *, name: str, city: str | None, category: str | None) -> str:
        location = city or "ישראל"
        biz_type = category or "עסק מקומי"
        return (
            f"צור תוכן שיווקי בעברית לאתר של עסק מקומי.\n"
            f"שם העסק: {name}\n"
            f"עיר: {location}\n"
            f"תחום: {biz_type}\n\n"
            f"החזר JSON בלבד עם המפתחות הבאים:\n"
            f"- hero_title: כותרת ראשית (עד 10 מילים)\n"
            f"- about_text: פסקת תיאור (2-3 משפטים)\n"
            f"- services_list: רשימת 3-5 שירותים (מערך של מחרוזות)\n"
            f"- tagline: סלוגן קצר (עד 6 מילים)\n\n"
            f"JSON בלבד, ללא הסברים."
        )

    def _parse_response(self, raw: str) -> SiteCopyResult | None:
        try:
            # Strip markdown code fences if present
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return SiteCopyResult(
                hero_title=str(data.get("hero_title", "")),
                about_text=str(data.get("about_text", "")),
                services_list=[str(s) for s in data.get("services_list", [])],
                tagline=str(data.get("tagline", "")),
            )
        except Exception:
            logger.warning("SiteCopyGeneratorService._parse_response: failed to parse LLM output", exc_info=True)
            return None

    def _fallback(self, *, name: str, city: str | None, category: str | None) -> SiteCopyResult:
        location = city or "ישראל"
        biz_type = category or "שירותים"
        return SiteCopyResult(
            hero_title=f"{name} — {biz_type} ב{location}",
            about_text=f"{name} הוא עסק מקומי מוביל בתחום {biz_type} ב{location}. אנו מתמחים במתן שירות מקצועי ואישי ללקוחותינו.",
            services_list=[f"שירותי {biz_type}", "ייעוץ מקצועי", "תמיכה אישית"],
            tagline=f"מקצועיות ואמינות — {name}",
        )
