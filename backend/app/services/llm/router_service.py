from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class LLMRouterService:
    def route(self, task_type: str) -> dict:
        default_map = {
            "generate_site_copy": {"provider": "openai", "review": "anthropic"},
            "review_generated_copy": {"provider": "anthropic", "review": None},
            "enrich_business_data": {"provider": "gemini", "review": None},
            "research_external_signal": {"provider": "xai", "review": None},
        }
        return default_map.get(task_type, {"provider": "openai", "review": None})

    def call(self, task_type: str, prompt: str, context: dict[str, Any] | None = None) -> str | None:
        """Call the LLM for a given task. Returns the text response or None on failure/not-configured."""
        from app.core.config import settings

        route = self.route(task_type)
        provider = route.get("provider", "openai")

        if provider == "openai" and settings.openai_api_key:
            return self._call_openai(prompt, settings.openai_api_key, settings.llm_default_model)

        logger.info("LLMRouterService.call: no API key configured for provider=%s task=%s — skipping", provider, task_type)
        return None

    def _call_openai(self, prompt: str, api_key: str, model: str) -> str | None:
        try:
            from openai import OpenAI  # type: ignore[import]
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception:
            logger.exception("LLMRouterService._call_openai failed")
            return None

