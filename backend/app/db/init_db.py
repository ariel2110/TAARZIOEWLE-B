from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.seed import seed_demo_data


def init_db() -> None:
    if not settings.auto_create_tables:
        return
    Base.metadata.create_all(bind=engine)
    if settings.auto_seed_demo_data:
        db = SessionLocal()
        try:
            seed_demo_data(db)
        finally:
            db.close()
