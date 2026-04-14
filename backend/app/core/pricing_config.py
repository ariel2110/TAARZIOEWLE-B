"""API Pricing Configuration — SiteNest
=========================================
All costs are in USD per 1,000,000 tokens (or flat per-unit for non-LLM tools).
Update these values when provider pricing changes.

Exchange rate: used to convert USD → ILS in cost calculations.
"""
from __future__ import annotations

# ─── Exchange rate ────────────────────────────────────────────────────────────
USD_TO_ILS: float = 3.70   # USD → ILS (update periodically)

# ─── Agent/model identifier → display info ───────────────────────────────────
# Keys must match the `agent_name` values written by log_usage_task.
AGENT_DISPLAY: dict[str, dict] = {
    'claude':  {'label': 'Claude (Anthropic)', 'color': '#d97706', 'emoji': '🟠'},
    'gpt':     {'label': 'GPT-4o (OpenAI)',    'color': '#10b981', 'emoji': '🟢'},
    'gemini':  {'label': 'Gemini (Google)',     'color': '#3b82f6', 'emoji': '🔵'},
    'grok':    {'label': 'Grok (xAI)',          'color': '#8b5cf6', 'emoji': '🟣'},
    'serper':  {'label': 'Serper Search',       'color': '#6b7280', 'emoji': '🔍'},
    'apify':   {'label': 'Apify Scraper',       'color': '#6b7280', 'emoji': '🕷️'},
}

# ─── Token pricing (USD per 1,000,000 tokens) ────────────────────────────────
TOKEN_PRICING: dict[str, dict[str, float]] = {
    # Agent key → {model hint, input $/1M, output $/1M}
    'claude': {
        'model':   'claude-3-5-sonnet / claude-sonnet-4-6',
        'input':   3.00,
        'output':  15.00,
    },
    'gpt': {
        'model':   'gpt-4o',
        'input':   5.00,
        'output':  15.00,
    },
    'gemini': {
        'model':   'gemini-1.5-flash / gemini-2.5-flash',
        'input':   0.075,
        'output':  0.30,
    },
    'grok': {
        'model':   'grok-2 / grok-3-mini',
        'input':   2.00,
        'output':  10.00,
    },
}

# ─── Flat-fee tools ───────────────────────────────────────────────────────────
SERPER_COST_PER_QUERY_USD: float = 0.001   # $0.001 per Google search query
APIFY_COST_PER_RUN_USD:    float = 0.005   # $0.005 per actor run

# ─── Subscription revenue (per site per month) ───────────────────────────────
PLAN_REVENUE_ILS: dict[str, float] = {
    'auto':    39.0,
    'starter': 299.0,
    'growth':  699.0,
    'pro':     1299.0,
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def calc_token_cost_usd(
    agent_name: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Return total USD cost for a single LLM call."""
    pricing = TOKEN_PRICING.get(agent_name)
    if not pricing:
        return 0.0
    cost = (input_tokens  / 1_000_000) * pricing['input'] \
         + (output_tokens / 1_000_000) * pricing['output']
    return round(cost, 8)


def usd_to_ils(usd: float) -> float:
    return round(usd * USD_TO_ILS, 6)


def estimate_tokens(text: str) -> int:
    """Rough token estimate when actual usage is unavailable (1 token ≈ 4 chars)."""
    return max(1, len(text) // 4)
