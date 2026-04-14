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

    page_fields = 'name,fan_count,followers_count'

    def _resolve_followers(data: dict) -> int | None:
        """Return followers_count if present, fall back to fan_count, else None."""
        fc = data.get('followers_count')
        if fc is not None:
            return fc
        return data.get('fan_count')

    def _safe_get(url: str, params: dict) -> tuple[int, dict]:
        """GET request returning (http_status, json_body). Never raises."""
        try:
            r = httpx.get(url, params=params, timeout=10)
            try:
                body = r.json()
            except Exception:
                body = {}
            return r.status_code, body
        except httpx.RequestError as exc:
            logger.error('Facebook Graph API request failed: %s', type(exc).__name__)
            return 0, {}

    def _is_token_expired(body: dict) -> bool:
        return body.get('error', {}).get('code') == 190

    def _fb_error_detail(body: dict) -> str:
        return body.get('error', {}).get('message', 'שגיאה לא ידועה')

    # ── Step 1: try /me/accounts — works for both User & Page tokens ──────────
    status_code, accounts_data = _safe_get(
        f'{_FB_BASE}/me/accounts',
        {'access_token': token, 'fields': f'id,access_token,{page_fields}'},
    )

    if status_code == 0:
        return FacebookStatsResponse(status='error', detail='שגיאת רשת — לא ניתן להגיע ל-Graph API')

    if _is_token_expired(accounts_data):
        logger.warning('Facebook token OAuthException (code 190) on /me/accounts')
        return FacebookStatsResponse(
            status='token_expired',
            detail='הטוקן פג תוקף — נדרש חידוש ב-Facebook Developers',
        )

    pages = accounts_data.get('data', [])
    if pages:
        # Use the first managed Page
        page = pages[0]
        page_id = page.get('id')
        page_token = page.get('access_token', token)

        # /me/accounts may already include followers_count/fan_count
        if page.get('followers_count') is not None or page.get('fan_count') is not None:
            return FacebookStatsResponse(
                status='active',
                page_name=page.get('name'),
                followers=_resolve_followers(page),
                fan_count=page.get('fan_count'),
            )

        # Otherwise fetch page details explicitly with the page token
        p_status, p_data = _safe_get(
            f'{_FB_BASE}/{page_id}',
            {'fields': page_fields, 'access_token': page_token},
        )
        if p_status == 200 and 'name' in p_data:
            return FacebookStatsResponse(
                status='active',
                page_name=p_data.get('name'),
                followers=_resolve_followers(p_data),
                fan_count=p_data.get('fan_count'),
            )
        if _is_token_expired(p_data):
            return FacebookStatsResponse(
                status='token_expired',
                detail='הטוקן פג תוקף — נדרש חידוש ב-Facebook Developers',
            )

    # ── Step 2: no managed pages — try /me directly (Page token case) ─────────
    me_status, me_data = _safe_get(
        f'{_FB_BASE}/me',
        {'fields': page_fields, 'access_token': token},
    )

    if me_status == 0:
        return FacebookStatsResponse(status='error', detail='שגיאת רשת — לא ניתן להגיע ל-Graph API')

    if _is_token_expired(me_data):
        logger.warning('Facebook token OAuthException (code 190) on /me')
        return FacebookStatsResponse(
            status='token_expired',
            detail='הטוקן פג תוקף — נדרש חידוש ב-Facebook Developers',
        )

    if me_status == 200 and 'name' in me_data:
        return FacebookStatsResponse(
            status='active',
            page_name=me_data.get('name'),
            followers=_resolve_followers(me_data),
            fan_count=me_data.get('fan_count'),
        )

    err_detail = _fb_error_detail(me_data) if 'error' in me_data else f'Facebook API שגיאה {me_status}'
    logger.error('Facebook Graph API final error: %s', err_detail)
    return FacebookStatsResponse(status='error', detail=err_detail)


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
