from sqlalchemy import JSON, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin, new_uuid
from app.models.enums import RegistrationStatus, ValidationStatus


class Registration(TimestampMixin, Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "academic_term_id", name="uq_registration_student_course_term"),
    )

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(GUID, ForeignKey("courses.id"), nullable=False)
    academic_term_id: Mapped[str] = mapped_column(GUID, ForeignKey("academic_terms.id"), nullable=False)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status"), nullable=False, default=RegistrationStatus.pending
    )
    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus, name="validation_status"), nullable=False, default=ValidationStatus.not_validated
    )
    validation_errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    student = relationship("Student")
    course = relationship("Course")
    academic_term = relationship("AcademicTerm")


class RegistrationValidationLog(TimestampMixin, Base):
    __tablename__ = "registration_validation_logs"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("students.id"), nullable=False, index=True)
    academic_term_id: Mapped[str] = mapped_column(GUID, ForeignKey("academic_terms.id"), nullable=False)
    requested_courses: Mapped[dict] = mapped_column(JSON, nullable=False)
    validation_result: Mapped[dict] = mapped_column(JSON, nullable=False)
