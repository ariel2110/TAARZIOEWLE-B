from urllib.parse import urlencode
from app.core.config import settings


class GoogleOAuthService:
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
            'note': 'Skeleton only: wire real Google OAuth verification before production use.',
        }
