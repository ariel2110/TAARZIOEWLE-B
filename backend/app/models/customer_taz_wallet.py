from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class CustomerTazWallet(Base, TimestampMixin):
    """Maps a customer phone number to their Vault wallet UUID."""
    __tablename__ = 'customer_taz_wallets'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    wallet_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    pending_order_ref: Mapped[str | None] = mapped_column(Text(), nullable=True)
