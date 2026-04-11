
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin

class PackageFieldPermission(Base, TimestampMixin):
    __tablename__ = 'package_field_permissions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_name: Mapped[str] = mapped_column(String(120), index=True)
    field_key: Mapped[str] = mapped_column(String(120), index=True)
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True)
    display_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
