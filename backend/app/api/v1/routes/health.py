from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.db.session import SessionLocal

router = APIRouter(tags=["health"])


@router.get('/health')
def health() -> dict:
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        try:
            db.close()
        except Exception:
            pass
    return {
        'status': 'ok' if db_ok else 'degraded',
        'service': settings.app_name,
        'env': settings.environment,
        'database_url_scheme': settings.effective_database_url.split(':', 1)[0],
        'database_ok': db_ok,
    }
