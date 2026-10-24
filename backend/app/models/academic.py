from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin, new_uuid
from app.models.enums import AcademicLevel


class AcademicTerm(Base):
    __tablename__ = "academic_terms"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    course_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_level: Mapped[AcademicLevel] = mapped_column(Enum(AcademicLevel, name="academic_level"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"
    __table_args__ = (UniqueConstraint("course_id", "prerequisite_course_id", name="uq_course_prereq"),)

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    course_id: Mapped[str] = mapped_column(GUID, ForeignKey("courses.id"), nullable=False)
    prerequisite_course_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("courses.id"), nullable=False
    )
    minimum_grade_points: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False, default=4.0)

    course = relationship("Course", foreign_keys=[course_id])
    prerequisite_course = relationship("Course", foreign_keys=[prerequisite_course_id])
