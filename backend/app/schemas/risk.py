from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AcademicLevel, RiskIndicatorType, RiskLevel, Severity


class RiskFactorOut(BaseModel):
    id: str
    factor_name: str
    observed_value: float | None
    threshold_value: float | None
    severity: Severity
    explanation: str
    recommended_action: str | None
    points_contributed: float

    model_config = {"from_attributes": True}


class RiskAssessmentOut(BaseModel):
    id: str
    student_id: str
    risk_score: float
    risk_level: RiskLevel
    assessment_date: datetime
    assessment_version: str
    summary: str | None
    data_completeness_note: str | None
    factors: list[RiskFactorOut] = []

    model_config = {"from_attributes": True}


class RiskRuleCreate(BaseModel):
    name: str
    description: str | None = None
    academic_level: AcademicLevel | None = None
    indicator_type: RiskIndicatorType
    threshold_value: float
    severity: Severity
    weight: float = 1.0
    is_active: bool = True


class RiskRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    academic_level: AcademicLevel | None = None
    threshold_value: float | None = None
    severity: Severity | None = None
    weight: float | None = None
    is_active: bool | None = None


class RiskRuleOut(BaseModel):
    id: str
    name: str
    description: str | None
    academic_level: AcademicLevel | None
    indicator_type: RiskIndicatorType
    threshold_value: float
    severity: Severity
    weight: float
    is_active: bool
    created_by: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}
