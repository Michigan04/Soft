from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, new_uuid, utcnow
from app.models.enums import AcademicLevel, RiskIndicatorType, RiskLevel, Severity


class RiskRule(Base):
    __tablename__ = "risk_rules"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    academic_level: Mapped[AcademicLevel | None] = mapped_column(
        Enum(AcademicLevel, name="academic_level"), nullable=True
    )
    indicator_type: Mapped[RiskIndicatorType] = mapped_column(
        Enum(RiskIndicatorType, name="risk_indicator_type"), nullable=False
    )
    threshold_value: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, name="severity"), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[str | None] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("students.id"), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), nullable=False, index=True)
    assessment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    assessment_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_completeness_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student")
    factors = relationship("RiskFactor", back_populates="assessment", order_by="desc(RiskFactor.severity)")


class RiskFactor(Base):
    __tablename__ = "risk_factors"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    assessment_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("risk_assessments.id"), nullable=False, index=True
    )
    rule_id: Mapped[str | None] = mapped_column(GUID, ForeignKey("risk_rules.id"), nullable=True)
    factor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, name="severity"), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    points_contributed: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    assessment = relationship("RiskAssessment", back_populates="factors")
    rule = relationship("RiskRule")
