from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

# provider string → agent_name used by cost_tracker
_PROVIDER_TO_AGENT: dict[str, str] = {
    "anthropic": "claude",
    "openai":    "gpt",
    "gemini":    "gemini",
    "xai":       "grok",
}


class LLMRouterService:
    """Routes LLM calls to the right provider based on task type.

    Provider specializations:
      gemini   — fast data analysis & extraction (Stage 1: Intelligence Analyst)
      openai   — creative Hebrew copywriting     (Stage 2: Brand Strategist)
      anthropic — HTML/CSS frontend generation   (Stage 3: Senior Developer)
    """

    TASK_PROVIDER_MAP: dict[str, str] = {
        # Pipeline stages
        "analyze_business_data":  "gemini",    # Stage 1b — Style & Design Director
        "generate_site_copy":     "openai",    # Stage 1a — Content Manager (GPT-4o primary, Grok fallback)
        "build_site_html":        "anthropic", # Stage 2  — Master Builder (Claude)
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
        text, _, _, _ = self._call_internal(
            task_type, prompt,
            system=system, model=model, max_tokens=max_tokens, json_mode=json_mode,
        )
        return text

    def call_tracked(
        self,
        task_type: str,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1200,
        json_mode: bool = False,
        business_id: int | None = None,
        draft_site_id: int | None = None,
        intake_token: str | None = None,
        stage: str | None = None,
    ) -> str | None:
        """Like ``call()`` but also fires an async cost-tracking event."""
        text, provider, model_used, (in_tok, out_tok) = self._call_internal(
            task_type, prompt,
            system=system, model=model, max_tokens=max_tokens, json_mode=json_mode,
        )
        if text is not None and provider:
            try:
                from app.services.cost_tracker import track_usage
                track_usage(
                    agent_name    = _PROVIDER_TO_AGENT.get(provider, provider),
                    model_name    = model_used,
                    input_tokens  = in_tok,
                    output_tokens = out_tok,
                    business_id   = business_id,
                    draft_site_id = draft_site_id,
                    intake_token  = intake_token,
                    stage         = stage,
                    task_type     = task_type,
                )
            except Exception:
                logger.warning("LLMRouterService: cost tracking failed silently", exc_info=True)
        return text

    def _call_internal(
        self,
        task_type: str,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1200,
        json_mode: bool = False,
    ) -> tuple[str | None, str | None, str | None, tuple[int, int]]:
        """
        Internal dispatcher.
        Returns (text, provider_used, model_used, (input_tokens, output_tokens)).
        """
        from app.core.config import settings

        primary = self.route(task_type)

        all_providers = [
            ("openai",    getattr(settings, "openai_api_key", None)),
            ("xai",       getattr(settings, "xai_api_key", None)),
            ("gemini",    getattr(settings, "gemini_api_key", None)),
            ("anthropic", getattr(settings, "anthropic_api_key", None)),
        ]
        ordered = [(p, k) for p, k in all_providers if p == primary] + \
                  [(p, k) for p, k in all_providers if p != primary]

        for provider, key in ordered:
            if not key:
                continue
            effective_model = model if provider == primary else None
            result: tuple[str | None, str | None, int, int] | None = None
            if provider == "xai":
                result = self._call_xai(
                    prompt, key,
                    model=effective_model or "grok-3-mini",
                    system=system, max_tokens=max_tokens, json_mode=json_mode,
                )
            elif provider == "gemini":
                result = self._call_gemini(
                    prompt, key,
                    model=effective_model or "gemini-2.5-flash",
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
                    system=system, max_tokens=max_tokens, json_mode=json_mode,
                )
            if result is not None:
                text, model_used, in_tok, out_tok = result
                if text is not None:
                    if provider != primary:
                        logger.info(
                            "LLMRouterService: used fallback provider=%s (primary=%s task=%s)",
                            provider, primary, task_type,
                        )
                    return text, provider, model_used, (in_tok, out_tok)

        logger.warning("LLMRouterService: all providers failed for task=%s", task_type)
        return None, None, None, (0, 0)



    # ── Provider implementations ──────────────────────────────────────────────
    # Each returns (text | None, model_name, input_tokens, output_tokens)

    def _call_xai(
        self, prompt: str, api_key: str, *,
        model: str = "grok-3-mini",
        system: str | None = None,
        max_tokens: int = 1200,
        json_mode: bool = False,
    ) -> tuple[str | None, str, int, int]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            messages: list[dict] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            kwargs: dict[str, Any] = dict(model=model, messages=messages, max_tokens=max_tokens, temperature=0.7)
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            in_tok  = getattr(resp.usage, 'prompt_tokens', 0) or 0
            out_tok = getattr(resp.usage, 'completion_tokens', 0) or 0
            return resp.choices[0].message.content, model, in_tok, out_tok
        except Exception:
            logger.exception("LLMRouterService._call_xai failed")
            return None, model, 0, 0

    def _call_openai(
        self, prompt: str, api_key: str, *,
        model: str = "gpt-4o",
        system: str | None = None,
        max_tokens: int = 1200,
        json_mode: bool = False,
    ) -> tuple[str | None, str, int, int]:
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
            in_tok  = getattr(resp.usage, 'prompt_tokens', 0) or 0
            out_tok = getattr(resp.usage, 'completion_tokens', 0) or 0
            return resp.choices[0].message.content, model, in_tok, out_tok
        except Exception:
            logger.exception("LLMRouterService._call_openai failed")
            return None, model, 0, 0

    def _call_anthropic(
        self, prompt: str, api_key: str, *,
        model: str = "claude-sonnet-4-6",
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> tuple[str | None, str, int, int]:
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
            in_tok  = getattr(resp.usage, 'input_tokens', 0) or 0
            out_tok = getattr(resp.usage, 'output_tokens', 0) or 0
            return resp.content[0].text, model, in_tok, out_tok
        except Exception:
            logger.exception("LLMRouterService._call_anthropic failed")
            return None, model, 0, 0

    def _call_gemini(
        self, prompt: str, api_key: str, *,
        model: str = "gemini-2.5-flash",
        system: str | None = None,
        max_tokens: int = 1200,
    ) -> tuple[str | None, str, int, int]:
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
            meta     = getattr(resp, 'usage_metadata', None)
            in_tok   = getattr(meta, 'prompt_token_count', 0) or 0
            out_tok  = getattr(meta, 'candidates_token_count', 0) or 0
            return resp.text, model, in_tok, out_tok
        except Exception:
            logger.exception("LLMRouterService._call_gemini failed")
            return None, model, 0, 0

