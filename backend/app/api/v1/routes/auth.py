from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.auth import CurrentAdminResponse, GoogleAuthStartResponse, DevLoginRequest, DevLoginResponse, GoogleVerifyRequest, GoogleVerifyResponse
from app.services.auth.google_oauth_service import GoogleOAuthService
from app.services.auth.auth_service import AuthService
from app.models.user import User
from app.core.config import settings
import httpx, os, logging

logger = logging.getLogger(__name__)

# In-memory store for captured YouTube refresh token (temporary)
_yt_token_store: dict = {}

router = APIRouter(prefix='/auth', tags=['auth'])
auth_service = AuthService()


@router.get('/me', response_model=CurrentAdminResponse)
def me(current_admin: User = Depends(get_current_admin)) -> CurrentAdminResponse:
    return CurrentAdminResponse(
        email=current_admin.email,
        full_name=current_admin.full_name,
        role=current_admin.role,
        auth_mode='bearer-jwt',
    )


@router.post('/dev-login', response_model=DevLoginResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)) -> DevLoginResponse:
    if settings.environment.lower() == 'production':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not found')
    if payload.admin_token != settings.admin_dev_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid admin token')
    user = auth_service.get_or_create_admin(db=db, email=payload.email, full_name=payload.full_name or 'Admin User')
    token = auth_service.create_admin_access_token(user.email)
    return DevLoginResponse(access_token=token, email=user.email, role=user.role)


@router.get('/google/start', response_model=GoogleAuthStartResponse)
def google_start() -> GoogleAuthStartResponse:
    data = GoogleOAuthService().build_auth_url()
    return GoogleAuthStartResponse(**data)


@router.get('/youtube/start', response_class=HTMLResponse)
def youtube_start():
    """Redirect directly to Google YouTube OAuth."""
    from urllib.parse import urlencode
    client_id = settings.google_client_id or ''
    redirect_uri = 'https://tazo-web.com/api/v1/auth/google/callback'
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': 'youtube',
    }
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return HTMLResponse(f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
  <meta charset="UTF-8"/>
  <title>TAZO — חיבור YouTube</title>
  <style>
    body {{
      margin:0; font-family:Heebo,Arial,sans-serif;
      background:#fff; display:flex;
      align-items:center; justify-content:center; min-height:100vh;
    }}
    .card {{
      text-align:center; padding:60px 40px;
      border-radius:20px; box-shadow:0 4px 32px rgba(0,0,0,.08);
      max-width:420px; width:100%;
    }}
    .logo {{ font-size:40px; margin-bottom:16px; }}
    h1 {{ font-size:22px; font-weight:800; color:#111; margin:0 0 8px; }}
    p {{ color:#888; font-size:14px; margin:0 0 32px; }}
    a.btn {{
      display:inline-flex; align-items:center; gap:10px;
      background:#FF0000; color:#fff; text-decoration:none;
      border-radius:50px; padding:14px 32px;
      font-size:16px; font-weight:700;
      box-shadow:0 4px 16px rgba(255,0,0,.3);
      transition:opacity .2s;
    }}
    a.btn:hover {{ opacity:.85; }}
    .yt-icon {{ width:22px; height:22px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">🎬</div>
    <h1>חיבור ערוץ YouTube ל-TAZO</h1>
    <p>לחץ כדי לאשר גישה לערוץ ה-YouTube שלך</p>
    <a class="btn" href="{url}">
      <svg class="yt-icon" viewBox="0 0 24 24" fill="white">
        <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1C24 15.9 24 12 24 12s0-3.9-.5-5.8zM9.7 15.5V8.5l6.3 3.5-6.3 3.5z"/>
      </svg>
      התחבר עם Google / YouTube
    </a>
  </div>
</body>
</html>""")


@router.get('/google/callback', response_class=HTMLResponse)
async def google_callback(request: Request, code: str = '', state: str = '', error: str = ''):
    """Handle Google OAuth callback — for YouTube or admin login."""
    if error:
        return HTMLResponse(f"<h1>Error: {error}</h1>", status_code=400)

    if not code:
        return HTMLResponse("<h1>No code received</h1>", status_code=400)

    if state == 'youtube':
        # Exchange code for tokens
        redirect_uri = 'https://tazo-web.com/api/v1/auth/google/callback'
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': settings.google_client_id,
                    'client_secret': settings.google_client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code',
                },
            )
        data = resp.json()
        refresh_token = data.get('refresh_token', '')
        access_token = data.get('access_token', '')

        if refresh_token:
            # Save to env file
            env_line = f'YOUTUBE_REFRESH_TOKEN={refresh_token}\n'
            with open('/app/.env', 'a') as f:
                f.write(env_line)
            _yt_token_store['refresh_token'] = refresh_token
            _yt_token_store['access_token'] = access_token
            logger.info("[YouTube OAuth] Refresh token saved successfully")

        return HTMLResponse(f"""
        <html><body style="font-family:Heebo,Arial;background:#0d1117;color:#22d3ee;text-align:center;padding:80px">
        <h1>{'✅ YouTube מחובר!' if refresh_token else '⚠️ לא התקבל Refresh Token'}</h1>
        <p style="color:#888">{'קוד הרענון נשמר — סגור חלון זה' if refresh_token else 'נסה שוב — ודא שבחרת חשבון עם ערוץ YouTube'}</p>
        {'<p style="font-size:11px;color:#333">Token: ' + refresh_token[:20] + '...</p>' if refresh_token else ''}
        </body></html>
        """)

    # Regular admin login flow
    return HTMLResponse("<script>window.close()</script>")


@router.get('/youtube/token')
def youtube_token_status():
    """Check if YouTube refresh token was captured."""
    rt = _yt_token_store.get('refresh_token', '')
    # Also check env
    if not rt:
        rt = os.environ.get('YOUTUBE_REFRESH_TOKEN', '')
    return {
        'connected': bool(rt),
        'token_preview': rt[:20] + '...' if rt else None,
    }


@router.post('/google/verify', response_model=GoogleVerifyResponse)
def google_verify(payload: GoogleVerifyRequest, db: Session = Depends(get_db)) -> GoogleVerifyResponse:
    """Verify a Google ID token from the frontend and return a JWT."""
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Google login is not configured on this server')
    try:
        info = GoogleOAuthService().verify_id_token(payload.id_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Google token')

    email: str = info['email']
    allowed = [e.strip().lower() for e in settings.allowed_admin_emails.split(',') if e.strip()]
    if allowed and email.lower() not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Email not authorized for admin access')

    user = auth_service.get_or_create_admin(db=db, email=email, full_name=info['full_name'])
    token = auth_service.create_admin_access_token(user.email)
    return GoogleVerifyResponse(access_token=token, email=user.email, full_name=user.full_name, role=user.role)
