from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class Cart(Base, TimestampMixin):
    """Ephemeral shopping cart keyed by browser session_id (cookie-based, no login required)."""
    __tablename__ = 'carts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    business_phone: Mapped[str] = mapped_column(String(50), index=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    items: Mapped[str | None] = mapped_column(Text(), nullable=True)   # JSON: [{name, qty, price, imageUrl}]
    delivery_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)  # in agora (1/100 ILS)
