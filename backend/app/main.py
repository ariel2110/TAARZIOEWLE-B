import app.models
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.init_db import init_db

app = FastAPI(title=settings.app_name)
_allowed_origins = [
    settings.frontend_admin_url,
    settings.frontend_customer_url,
    settings.frontend_public_url,
]
# In development allow localhost variants on common ports
if settings.environment != 'production':
    _allowed_origins += [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:5175',
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'X-Admin-Token', 'X-Admin-Email', 'X-Session-Key'],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)

static_dir = Path(__file__).resolve().parent / 'static_sites'
static_dir.mkdir(parents=True, exist_ok=True)
app.mount('/static', StaticFiles(directory=str(static_dir)), name='static')


@app.on_event('startup')
def on_startup() -> None:
    init_db()


import re as _re
_SUBDOMAIN_RE = _re.compile(r'^(?!(?:api|admin|www|portal|evolution|customer)\.)[^.]+\.tazo-web\.com(?::\d+)?$', _re.I)


@app.get('/')
@app.get('/{path:path}')
def root_or_site(request: Request, path: str = ''):
    host = request.headers.get('host', '')
    if _SUBDOMAIN_RE.match(host):
        # Subdomain request — delegate to site-by-host handler
        from app.api.v1.routes.public_sites import site_by_host
        from app.db.session import get_db as _get_db
        db = next(_get_db())
        return site_by_host(request, db)
    return {
        'service': settings.app_name,
        'status': 'ok',
        'api_prefix': settings.api_v1_prefix,
        'database_url_scheme': settings.effective_database_url.split(':', 1)[0],
    }
