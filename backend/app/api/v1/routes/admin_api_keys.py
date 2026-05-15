"""
Admin API Keys Management
Allows viewing (masked) and updating/deleting API tokens from the admin dashboard.
"""
import logging
import pathlib
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_admin
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/admin/api-keys', tags=['admin-api-keys'])

# ---------------------------------------------------------------------------
# Key catalog — (category, settings_field, display_label, env_var_name, role, manage_url)
# ---------------------------------------------------------------------------
_CATALOG: list[tuple[str, str, str, str, str, str]] = [
    ('LLM', 'openai_api_key',         'GPT-4o (OpenAI)',        'OPENAI_API_KEY',          'כותב תוכן — קופירייטינג לאתרים',           'https://platform.openai.com/api-keys'),
    ('LLM', 'anthropic_api_key',      'Claude (Anthropic)',     'ANTHROPIC_API_KEY',        'אדריכל WOW — בניית מבנה אתר יצירתי',       'https://console.anthropic.com/settings/keys'),
    ('LLM', 'gemini_api_key',         'Gemini (Google AI)',     'GEMINI_API_KEY',            'סינון וניתוח — מסנן לידים ועיבוד נתונים',  'https://aistudio.google.com/app/apikey'),
    ('LLM', 'xai_api_key',            'Grok (xAI)',             'XAI_API_KEY',              'מנהל מכירות — תגובות WhatsApp וסגירות',     'https://console.x.ai/team/credits'),
    ('חיפוש ונתונים', 'google_places_api_key', 'Google Places API', 'GOOGLE_PLACES_API_KEY', 'איסוף לידים — חיפוש עסקים לפי קטגוריה',   'https://console.cloud.google.com/apis/credentials'),
    ('חיפוש ונתונים', 'serper_api_key',        'Serper.dev',        'SERPER_API_KEY',          'גוגל סרץ\' — חיפוש אינטרנט עבור הסוכנים', 'https://serper.dev/dashboard'),
    ('חיפוש ונתונים', 'apify_api_token',       'Apify',             'APIFY_API_TOKEN',         'סקרייפינג — חילוץ מידע מאינסטגרם/טיקטוק', 'https://console.apify.com/account/settings/integrations'),
    ('חיפוש ונתונים', 'facebook_access_token', 'Facebook Graph API','FACEBOOK_ACCESS_TOKEN',   'פייסבוק — גישה לעמודים עסקיים',           'https://developers.facebook.com/tools/debug/accesstoken'),
    ('WhatsApp', 'meta_wa_phone_number_id', 'Meta Phone Number ID',  'META_WA_PHONE_NUMBER_ID', 'מזהה מספר הטלפון ב-Meta Business Manager', 'https://business.facebook.com/wa/manage/phone-numbers/'),
    ('WhatsApp', 'meta_wa_access_token',    'Meta Access Token',     'META_WA_ACCESS_TOKEN',    'System User Permanent Token — WhatsApp Cloud API', 'https://business.facebook.com/settings/system-users/'),
    ('WhatsApp', 'whatsapp_verify_token',   'Webhook Verify Token',  'WHATSAPP_VERIFY_TOKEN',   'טוקן אימות Webhook — נדרש ב-Meta Developers', ''),
    ('תשלומים', 'morning_api_key',           'Morning API Key',             'MORNING_API_KEY',           'תשלומים — יצירת חשבוניות ולינקי תשלום',                    'https://app.greeninvoice.co.il/settings/developers/api'),
    ('תשלומים', 'morning_api_secret',        'Morning API Secret',          'MORNING_API_SECRET',        'חתימת בקשות API מול Morning',                               'https://app.greeninvoice.co.il/settings/developers/api'),
    ('תשלומים', 'morning_webhook_secret',    'Morning Webhook Secret',      'MORNING_WEBHOOK_SECRET',    'אימות Webhook של Morning — טריגר דומיין',                   'https://app.greeninvoice.co.il/settings/developers/webhooks'),
    ('תשלומים', 'morning_fixed_payment_url', 'Morning Payment URL (Auto)',  'MORNING_FIXED_PAYMENT_URL', 'לינק תשלום קבוע לתוכנית Auto (₪39)',                        'https://app.greeninvoice.co.il'),
    ('תשתית',   'hostinger_api_token',       'Hostinger API Token',         'HOSTINGER_API_TOKEN',       'רישום דומיינים ו-DNS אוטומטי',                              'https://hpanel.hostinger.com/profile/api'),
]

_ALLOWED_KEYS: dict[str, tuple] = {item[1]: item for item in _CATALOG}

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
    for cat, field, label, env_var, role, manage_url in _CATALOG:
        current_val = getattr(settings, field, None)
        # Non-secret fields (URLs) show value in plain text, not masked
        is_url_field = field.endswith('_url')
        groups_map.setdefault(cat, []).append({
            'key':        field,
            'label':      label,
            'env_var':    env_var,
            'role':       role,
            'manage_url': manage_url,
            'configured': bool(current_val),
            'masked':     str(current_val) if (is_url_field and current_val) else _mask(current_val),
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
    admin: User = Depends(get_current_admin),
):
    """Update or clear an API key. Send value=null or value='' to delete."""
    if key_name not in _ALLOWED_KEYS:
        raise HTTPException(status_code=400, detail=f'Unknown key: {key_name}')

    entry = _ALLOWED_KEYS[key_name]
    env_var = entry[3]

    # Normalise: blank string → treat as delete
    new_value: str | None = (body.value or '').strip() or None
    action = 'delete' if new_value is None else 'update'

    # 1. Persist to .env (survives restarts)
    _update_env_file(env_var, new_value)

    # 2. Update in-memory settings so change takes effect immediately
    setattr(settings, key_name, new_value)

    # 3. Audit log — who changed what and when
    admin_email = getattr(admin, 'email', 'unknown')
    logger.warning(
        '[APIKeyAudit] user=%s action=%s key=%s env_var=%s at=%s',
        admin_email, action, key_name, env_var,
        datetime.now(timezone.utc).isoformat(),
    )

    return {
        'key':        key_name,
        'configured': bool(new_value),
        'masked':     _mask(new_value),
    }
