from urllib.parse import urlencode
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings


class GoogleOAuthService:
    def verify_id_token(self, token: str) -> dict:
        """Verify a Google ID token and return the payload (email, name, sub)."""
        if not settings.google_client_id:
            raise ValueError('GOOGLE_CLIENT_ID is not configured')
        idinfo = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
        return {
            'email': idinfo['email'],
            'full_name': idinfo.get('name', idinfo['email']),
            'email_verified': idinfo.get('email_verified', False),
        }

    def build_auth_url(self) -> dict:
        state = 'dev-google-oauth-state'
        params = {
            'client_id': settings.google_client_id or 'missing-google-client-id',
            'redirect_uri': settings.google_oauth_redirect_url,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent',
        }
        return {
            'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params),
            'state': state,
            'enabled': bool(settings.google_client_id),
        }
