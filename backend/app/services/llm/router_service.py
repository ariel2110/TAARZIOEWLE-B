from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class LLMRouterService:
    """Routes LLM calls to the right provider based on task type.

    Provider specializations:
      gemini   — fast data analysis & extraction (Stage 1: Intelligence Analyst)
      openai   — creative Hebrew copywriting     (Stage 2: Brand Strategist)
      anthropic — HTML/CSS frontend generation   (Stage 3: Senior Developer)
    """

    TASK_PROVIDER_MAP: dict[str, str] = {
        # Pipeline stages
        "analyze_business_data":  "gemini",    # Stage 1 — Intelligence Analyst
        "generate_site_copy":     "openai",    # Stage 2 — Brand Strategist & Copywriter
        "build_site_html":        "anthropic", # Stage 3 — Senior Frontend Developer
        # Legacy / standalone tasks
        "review_generated_copy":  "anthropic",
        "enrich_business_data":   "gemini",
        "research_external_signal": "openai",
    }

    def route(self, task_type: str) -> str:
        return self.TASK_PROVIDER_MAP.get(task_type, "openai")

    def call(
        self,
        task_type: str,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1200,
        json_mode: bool = False,
        context: dict[str, Any] | None = None,
    ) -> str | None:
        """Route a prompt to the right provider. Falls back to other providers on failure."""
        from app.core.config import settings

        primary = self.route(task_type)

        # Build candidate list: preferred provider first, then fallbacks
        all_providers = [
            ("gemini",    getattr(settings, "gemini_api_key", None)),
            ("openai",    getattr(settings, "openai_api_key", None)),
            ("anthropic", getattr(settings, "anthropic_api_key", None)),
        ]
        ordered = [(p, k) for p, k in all_providers if p == primary] + \
                  [(p, k) for p, k in all_providers if p != primary]

        for provider, key in ordered:
            if not key:
                continue
            # Use caller's model hint only for the primary provider; fallbacks use their own defaults
            effective_model = model if provider == primary else None
            result: str | None = None
            if provider == "gemini":
                result = self._call_gemini(
                    prompt, key,
                    model=effective_model or "gemini-2.0-flash",
                    system=system, max_tokens=max_tokens,
                )
            elif provider == "anthropic":
                result = self._call_anthropic(
                    prompt, key,
                    model=effective_model or "claude-sonnet-4-6",
                    system=system, max_tokens=max_tokens,
                )
            elif provider == "openai":
                result = self._call_openai(
                    prompt, key,
                    model=effective_model or settings.llm_default_model,
                    system=system, max_tokens=max_tokens,
                    json_mode=json_mode,
                )
            if result is not None:
                if provider != primary:
                    logger.info("LLMRouterService: used fallback provider=%s (primary=%s task=%s)", provider, primary, task_type)
                return result

        logger.warning("LLMRouterService: all providers failed for task=%s", task_type)
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Provider implementations
    # ──────────────────────────────────────────────────────────────────────────

    def _call_openai(
        self, prompt: str, api_key: str, *,
        model: str = "gpt-4o",
        system: str | None = None,
        max_tokens: int = 1200,
        json_mode: bool = False,
    ) -> str | None:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            messages: list[dict] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            kwargs: dict[str, Any] = dict(model=model, messages=messages, max_tokens=max_tokens, temperature=0.7)
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception:
            logger.exception("LLMRouterService._call_openai failed")
            return None

    def _call_anthropic(
        self, prompt: str, api_key: str, *,
        model: str = "claude-sonnet-4-6",
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> str | None:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            kwargs: dict[str, Any] = dict(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            if system:
                kwargs["system"] = system
            resp = client.messages.create(**kwargs)
            return resp.content[0].text
        except Exception:
            logger.exception("LLMRouterService._call_anthropic failed")
            return None

    def _call_gemini(
        self, prompt: str, api_key: str, *,
        model: str = "gemini-2.0-flash",
        system: str | None = None,
        max_tokens: int = 1200,
    ) -> str | None:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            contents = f"{system}\n\n{prompt}" if system else prompt
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,
                ),
            )
            return resp.text
        except Exception:
            logger.exception("LLMRouterService._call_gemini failed")
            return None

