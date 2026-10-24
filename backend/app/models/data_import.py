from datetime import datetime

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, new_uuid, utcnow
from app.models.enums import ImportStatus, ImportType


class DataImport(Base):
    __tablename__ = "data_imports"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    uploaded_by: Mapped[str | None] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    import_type: Mapped[ImportType] = mapped_column(Enum(ImportType, name="import_type"), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, name="import_status"), nullable=False, default=ImportStatus.pending
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    validated_rows: Mapped[list | None] = mapped_column(JSON, nullable=True)
    row_errors: Mapped[list | None] = mapped_column(JSON, nullable=True)

    uploader = relationship("User")
