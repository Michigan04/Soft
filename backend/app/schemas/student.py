from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import AcademicLevel, ProgramStatus, RiskLevel


class StudentListItem(BaseModel):
    id: str
    student_identifier: str
    full_name: str
    academic_level: AcademicLevel
    program_status: ProgramStatus
    current_term: str | None
    assigned_staff_id: str | None
    assigned_staff_name: str | None = None
    cgpa: float | None = None
    latest_risk_level: RiskLevel | None = None
    latest_risk_score: float | None = None
    primary_risk_reason: str | None = None
    latest_assessment_date: datetime | None = None
    pending_followups: int = 0

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    email: str
    password: str
    full_name: str
    student_identifier: str
    academic_level: AcademicLevel
    admission_date: date
    current_term: str | None = None


class StudentUpdate(BaseModel):
    full_name: str | None = None
    academic_level: AcademicLevel | None = None
    program_status: ProgramStatus | None = None
    current_term: str | None = None


class StudentDetail(BaseModel):
    id: str
    student_identifier: str
    full_name: str
    academic_level: AcademicLevel
    program_status: ProgramStatus
    admission_date: date
    current_term: str | None
    assigned_staff_id: str | None
    assigned_staff_name: str | None = None

    model_config = {"from_attributes": True}
