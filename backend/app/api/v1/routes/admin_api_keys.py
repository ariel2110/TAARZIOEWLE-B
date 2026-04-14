"""
Admin API Keys Management
Allows viewing (masked) and updating/deleting API tokens from the admin dashboard.
"""
import pathlib
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_admin
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix='/admin/api-keys', tags=['admin-api-keys'])

# ---------------------------------------------------------------------------
# Key catalog — (category, settings_field, display_label, env_var_name)
# ---------------------------------------------------------------------------
_CATALOG: list[tuple[str, str, str, str]] = [
    ('LLM',           'openai_api_key',          'GPT (OpenAI)',              'OPENAI_API_KEY'),
    ('LLM',           'anthropic_api_key',        'Claude (Anthropic)',        'ANTHROPIC_API_KEY'),
    ('LLM',           'gemini_api_key',            'Gemini (Google AI)',        'GEMINI_API_KEY'),
    ('LLM',           'xai_api_key',              'Grok (xAI)',                'XAI_API_KEY'),
    ('חיפוש ונתונים', 'google_places_api_key',    'Google Places API',         'GOOGLE_PLACES_API_KEY'),
    ('חיפוש ונתונים', 'serper_api_key',           'Serper (Google Search)',    'SERPER_API_KEY'),
    ('חיפוש ונתונים', 'apify_api_token',          'Apify (Web Scraping)',      'APIFY_API_TOKEN'),
    ('חיפוש ונתונים', 'facebook_access_token',    'Facebook Access Token',     'FACEBOOK_ACCESS_TOKEN'),
    ('WhatsApp',      'evolution_api_url',         'Evolution URL',             'EVOLUTION_API_URL'),
    ('WhatsApp',      'evolution_api_key',         'Evolution API Key',         'EVOLUTION_API_KEY'),
    ('WhatsApp',      'evolution_instance',        'Evolution Instance',        'EVOLUTION_INSTANCE'),
    ('תשלומים',       'morning_api_key',           'Morning API Key',           'MORNING_API_KEY'),
    ('תשלומים',       'morning_api_secret',        'Morning API Secret',        'MORNING_API_SECRET'),
    ('תשלומים',       'morning_webhook_secret',    'Morning Webhook Secret',    'MORNING_WEBHOOK_SECRET'),
    ('תשתית',         'hostinger_api_token',       'Hostinger API Token',       'HOSTINGER_API_TOKEN'),
]

_ALLOWED_KEYS: dict[str, tuple[str, str, str, str]] = {item[1]: item for item in _CATALOG}

# .env lives at the project backend root (4 levels up from this routes/ dir)
_ENV_FILE = pathlib.Path(__file__).parents[4] / '.env'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask(value: str | None) -> str:
    """Return a masked representation — never expose the full value."""
    if not value:
        return ''
    if len(value) <= 8:
        return '****'
    return f'****...{value[-4:]}'


def _update_env_file(env_var: str, value: str | None) -> None:
    """Update or add/remove a KEY=value line in the .env file."""
    if _ENV_FILE.exists():
        lines = _ENV_FILE.read_text(encoding='utf-8').splitlines(keepends=True)
    else:
        lines = []

    new_line = f'{env_var}={value}\n' if value else None
    found = False
    new_lines: list[str] = []

    for line in lines:
        if re.match(rf'^{re.escape(env_var)}\s*=', line):
            found = True
            if new_line:
                new_lines.append(new_line)
            # if value is None → omit the line (deletes the key)
        else:
            new_lines.append(line)

    if not found and new_line:
        # Append a trailing newline if file doesn't end with one
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        new_lines.append(new_line)

    _ENV_FILE.write_text(''.join(new_lines), encoding='utf-8')


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class UpdateKeyRequest(BaseModel):
    value: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get('')
def list_api_keys(_: User = Depends(get_current_admin)):
    """Return all API keys grouped by category (values are masked)."""
    groups_map: dict[str, list[dict]] = {}
    for cat, field, label, env_var in _CATALOG:
        current_val = getattr(settings, field, None)
        groups_map.setdefault(cat, []).append({
            'key':        field,
            'label':      label,
            'env_var':    env_var,
            'configured': bool(current_val),
            'masked':     _mask(current_val),
        })
    return {
        'groups': [
            {'category': cat, 'keys': keys}
            for cat, keys in groups_map.items()
        ]
    }


@router.put('/{key_name}')
def update_api_key(
    key_name: str,
    body: UpdateKeyRequest,
    _: User = Depends(get_current_admin),
):
    """Update or clear an API key. Send value=null or value='' to delete."""
    if key_name not in _ALLOWED_KEYS:
        raise HTTPException(status_code=400, detail=f'Unknown key: {key_name}')

    entry = _ALLOWED_KEYS[key_name]
    env_var = entry[3]

    # Normalise: blank string → treat as delete
    new_value: str | None = (body.value or '').strip() or None

    # 1. Persist to .env (survives restarts)
    _update_env_file(env_var, new_value)

    # 2. Update in-memory settings so change takes effect immediately
    setattr(settings, key_name, new_value)

    return {
        'key':        key_name,
        'configured': bool(new_value),
        'masked':     _mask(new_value),
    }
