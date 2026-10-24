from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, GUID, new_uuid, utcnow


class PolicySetting(Base):
    """Generic, admin-configurable key/value policy store.

    Used for values that are policy decisions rather than per-indicator rules,
    e.g. risk-score-to-level thresholds and CGPA projection assumptions (US-09).
    """

    __tablename__ = "policy_settings"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)
