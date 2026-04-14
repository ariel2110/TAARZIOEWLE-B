"""
Admin Social — Facebook Graph API integration.
Fetches page follower count and business name using a Long-lived Page Token.
"""
import logging
from typing import Literal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_admin
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/admin/social', tags=['admin-social'])

_FB_API_VERSION = 'v19.0'
_FB_BASE = f'https://graph.facebook.com/{_FB_API_VERSION}'

# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class FacebookStatsResponse(BaseModel):
    status: Literal['active', 'no_token', 'token_expired', 'error']
    page_name: str | None = None
    followers: int | None = None
    fan_count: int | None = None
    detail: str | None = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get('/facebook-stats', response_model=FacebookStatsResponse)
def facebook_stats(_: User = Depends(get_current_admin)) -> FacebookStatsResponse:
    """
    Fetch Facebook Page stats for the configured token.
    Returns follower_count, fan_count, and page name.
    Handles 401 (expired token) distinctly so the frontend can alert the user.
    The token is never written to logs.
    """
    token = settings.facebook_access_token
    if not token:
        return FacebookStatsResponse(status='no_token', detail='FACEBOOK_ACCESS_TOKEN לא מוגדר ב-.env')

    fields = 'name,followers_count,fan_count'
    url = f'{_FB_BASE}/me'

    try:
        resp = httpx.get(
            url,
            params={'fields': fields, 'access_token': token},
            timeout=10,
        )
    except httpx.RequestError as exc:
        logger.error('Facebook Graph API request failed: %s', type(exc).__name__)
        return FacebookStatsResponse(status='error', detail='שגיאת רשת — לא ניתן להגיע ל-Graph API')

    if resp.status_code == 401:
        logger.warning('Facebook token returned 401 — token may be expired or invalid')
        return FacebookStatsResponse(
            status='token_expired',
            detail='הטוקן פג תוקף — נדרש חידוש ב-Facebook Developers',
        )

    if not resp.is_success:
        logger.error('Facebook Graph API returned HTTP %d', resp.status_code)
        return FacebookStatsResponse(
            status='error',
            detail=f'Facebook API שגיאה {resp.status_code}',
        )

    data = resp.json()

    if 'error' in data:
        err = data['error']
        code = err.get('code')
        # Error code 190 = OAuthException (token invalid/expired)
        if code == 190:
            logger.warning('Facebook token OAuthException (code 190) — token may be expired')
            return FacebookStatsResponse(
                status='token_expired',
                detail='הטוקן פג תוקף — נדרש חידוש ב-Facebook Developers',
            )
        logger.error('Facebook Graph API error: code=%s type=%s', code, err.get('type'))
        return FacebookStatsResponse(status='error', detail=err.get('message', 'שגיאה לא ידועה'))

    return FacebookStatsResponse(
        status='active',
        page_name=data.get('name'),
        followers=data.get('followers_count'),
        fan_count=data.get('fan_count'),
    )


# ---------------------------------------------------------------------------
# Manual token refresh trigger
# ---------------------------------------------------------------------------

class TokenRefreshResponse(BaseModel):
    triggered: bool
    task_id: str | None = None
    detail: str | None = None


@router.post('/facebook-refresh-token', response_model=TokenRefreshResponse)
def facebook_refresh_token(_: User = Depends(get_current_admin)) -> TokenRefreshResponse:
    """
    Manually trigger a Facebook long-lived token refresh.
    The task runs asynchronously — check Celery logs for result.
    Requires FACEBOOK_APP_ID and FACEBOOK_APP_SECRET to be set in .env.
    """
    from app.tasks import facebook_token_refresh_task

    app_id = settings.facebook_app_id
    app_secret = settings.facebook_app_secret

    if not app_id or not app_secret:
        return TokenRefreshResponse(
            triggered=False,
            detail='חסרים FACEBOOK_APP_ID ו/או FACEBOOK_APP_SECRET ב-.env',
        )

    result = facebook_token_refresh_task.apply_async()
    logger.info('Manual Facebook token refresh triggered, task_id=%s', result.id)
    return TokenRefreshResponse(triggered=True, task_id=result.id)
