"""agent_toggle_service.py
=========================
Service layer for enabling/disabling AI agents and computing
smart role assignments for the site-generation pipeline.

Pipeline stage assignments (6 parallel agents):
  content  — gpt > grok > deepseek > mistral > gemini > claude
  design   — gemini > claude > gpt > grok > mistral > deepseek
  html     — claude > gpt > gemini > grok > mistral > deepseek
  seo      — mistral > gpt > grok > deepseek > gemini > claude
  cro      — cohere > gpt > grok > deepseek > mistral > gemini
  enrich   — deepseek > grok > mistral > gpt > gemini > claude
  social   — grok > claude > gpt > gemini > mistral > deepseek
"""
from __future__ import annotations

import datetime
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Map agent name → provider string used by router_service / cost_tracker
AGENT_TO_PROVIDER: dict[str, str] = {
    "claude":   "anthropic",
    "gpt":      "openai",
    "gemini":   "gemini",
    "grok":     "xai",
    "deepseek": "deepseek",
    "mistral":  "mistral",
    "cohere":   "cohere",
}

# Reverse map: provider → agent
PROVIDER_TO_AGENT: dict[str, str] = {v: k for k, v in AGENT_TO_PROVIDER.items()}

# All LLM agents (serper/apify are tools, not LLMs)
ALL_LLM_AGENTS = list(AGENT_TO_PROVIDER.keys())

# Agents seeded as disabled by default (must be enabled manually from dashboard)
DEFAULT_DISABLED_AGENTS: set[str] = set()  # all agents start enabled

# Best-to-fallback priority per pipeline stage
STAGE_PRIORITY: dict[str, list[str]] = {
    "content": ["gpt", "grok", "deepseek", "mistral", "gemini", "claude"],
    "design":  ["gemini", "claude", "gpt", "grok", "mistral", "deepseek"],
    "html":    ["claude", "gpt", "gemini", "grok", "mistral", "deepseek"],
    "seo":     ["mistral", "gpt", "grok", "deepseek", "gemini", "claude"],
    "cro":     ["cohere", "gpt", "grok", "deepseek", "mistral", "gemini"],
    "enrich":  ["deepseek", "grok", "mistral", "gpt", "gemini", "claude"],
    "social":  ["grok", "claude", "gpt", "gemini", "mistral", "deepseek"],
}

# Human-readable stage labels
STAGE_LABELS: dict[str, str] = {
    "content": "📄 תוכן",
    "design":  "🎨 עיצוב",
    "html":    "🔨 HTML",
    "seo":     "🔍 SEO",
    "cro":     "💡 המרה",
    "enrich":  "📊 העשרה",
    "social":  "💬 עדויות",
}


def _ensure_seeded(db: Session) -> None:
    """Insert default rows if missing. Cohere is seeded as disabled."""
    from app.models.agent_toggle import AgentToggle
    existing = {r.agent_name for r in db.query(AgentToggle).all()}
    for name in ALL_LLM_AGENTS:
        if name not in existing:
            enabled = name not in DEFAULT_DISABLED_AGENTS
            db.add(AgentToggle(agent_name=name, is_enabled=enabled))
    if len(existing) != len(ALL_LLM_AGENTS):
        db.commit()


def get_all_toggles(db: Session) -> dict[str, bool]:
    """Returns {agent_name: is_enabled} for all LLM agents."""
    from app.models.agent_toggle import AgentToggle
    _ensure_seeded(db)
    rows = db.query(AgentToggle).all()
    base = {a: True for a in ALL_LLM_AGENTS}
    for row in rows:
        base[row.agent_name] = row.is_enabled
    return base


def toggle_agent(db: Session, agent_name: str, enabled: bool) -> dict:
    """Enable or disable an agent. Returns updated toggle info."""
    from app.models.agent_toggle import AgentToggle
    if agent_name not in ALL_LLM_AGENTS:
        raise ValueError(f"Unknown agent: {agent_name}")

    _ensure_seeded(db)
    row = db.query(AgentToggle).filter(AgentToggle.agent_name == agent_name).first()
    if not row:
        row = AgentToggle(agent_name=agent_name, is_enabled=enabled)
        db.add(row)
    else:
        row.is_enabled = enabled
        row.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(row)
    return {"agent_name": row.agent_name, "is_enabled": row.is_enabled}


def get_build_config(db: Session) -> dict:
    """
    Returns the current build configuration:
      - enabled_agents: list of enabled LLM agent names
      - roles: {stage: agent_name} — which agent handles each pipeline stage
      - role_labels: {stage: label} — human-readable labels
      - provider_map: {stage: provider} — provider names for router_service

    Safety guarantee: even if all agents are disabled, roles fall back to
    the first configured (API key present) agent.
    """
    from app.core.config import settings

    toggles = get_all_toggles(db)
    enabled = [a for a in ALL_LLM_AGENTS if toggles.get(a, True)]

    # Respect API key presence too — an agent without a key can't work
    api_key_map = {
        "claude":   bool(getattr(settings, "anthropic_api_key", None)),
        "gpt":      bool(getattr(settings, "openai_api_key", None)),
        "gemini":   bool(getattr(settings, "gemini_api_key", None)),
        "grok":     bool(getattr(settings, "xai_api_key", None)),
        "deepseek": bool(getattr(settings, "deepseek_api_key", None)),
        "mistral":  bool(getattr(settings, "mistral_api_key", None)),
        "cohere":   bool(getattr(settings, "cohere_api_key", None)),
    }
    available = [a for a in enabled if api_key_map.get(a, False)]

    # Ultimate fallback: if nothing available, use any configured agent
    if not available:
        available = [a for a in ALL_LLM_AGENTS if api_key_map.get(a, False)]
    if not available:
        available = ALL_LLM_AGENTS[:1]  # last resort

    roles: dict[str, str] = {}
    for stage, priority in STAGE_PRIORITY.items():
        # Pick the highest-priority available agent for this stage
        chosen = next((a for a in priority if a in available), available[0])
        roles[stage] = chosen

    return {
        "enabled_agents": enabled,
        "available_agents": available,
        "roles": roles,
        "role_labels": {stage: STAGE_LABELS[stage] for stage in roles},
        "provider_map": {stage: AGENT_TO_PROVIDER[agent] for stage, agent in roles.items()},
    }


def get_enabled_providers_from_db() -> set[str] | None:
    """
    Opens its own DB session and returns the set of enabled provider names.
    Called by router_service during LLM dispatch.
    Returns None if no restrictions should apply (all enabled or error).
    """
    try:
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            from app.models.agent_toggle import AgentToggle
            rows = db.query(AgentToggle).all()
            if not rows:
                return None  # table empty → no restrictions
            enabled_agents = {r.agent_name for r in rows if r.is_enabled}
            if len(enabled_agents) == len(ALL_LLM_AGENTS):
                return None  # all enabled → no filtering needed
            providers = {AGENT_TO_PROVIDER[a] for a in enabled_agents if a in AGENT_TO_PROVIDER}
            return providers if providers else None  # all disabled → safety: unrestricted
        finally:
            db.close()
    except Exception:
        logger.debug("agent_toggle_service: DB lookup failed — using all providers", exc_info=True)
        return None
