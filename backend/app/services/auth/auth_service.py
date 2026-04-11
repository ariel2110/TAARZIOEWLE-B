from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token


class AuthService:
    def get_or_create_admin(self, db: Session, email: str, full_name: str = 'Admin User') -> User:
        user = db.query(User).filter(User.email == email).first()
        if user:
            if full_name and not user.full_name:
                user.full_name = full_name
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        user = User(email=email, full_name=full_name, role='admin', is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def create_admin_access_token(self, email: str) -> str:
        return create_access_token(subject=email, role='admin')
