from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Lead(Base):
    """
    One funder or partner lead. Populated by load_data.py from the agent
    pipeline's affa_crm.db; served read/write from here on.
    """

    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("name", name="uq_leads_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(16), index=True)  # 'funder' | 'partner'
    name: Mapped[str] = mapped_column(String(255), index=True)
    subtype: Mapped[Optional[str]] = mapped_column(String(64), default="")
    focus_area: Mapped[Optional[str]] = mapped_column(Text, default="")
    fit_reason: Mapped[Optional[str]] = mapped_column(Text, default="")
    url: Mapped[Optional[str]] = mapped_column(String(512), default="")

    contact_name: Mapped[Optional[str]] = mapped_column(String(255), default="")
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), default="")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(64), default="")
    contact_page: Mapped[Optional[str]] = mapped_column(String(512), default="")

    outreach_message: Mapped[Optional[str]] = mapped_column(Text, default="")
    # new -> contacted -> responded -> declined (free text, not an enum, so
    # the pipeline's existing 'drafted' status from build_crm.py still fits)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)

    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)
