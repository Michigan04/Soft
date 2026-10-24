from datetime import date

from pydantic import BaseModel

from app.models.enums import AcademicLevel, ResultStatus


class AcademicTermOut(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date
    is_active: bool

    model_config = {"from_attributes": True}


class CourseOut(BaseModel):
    id: str
    course_code: str
    course_name: str
    credits: int
    academic_level: AcademicLevel
    is_active: bool

    model_config = {"from_attributes": True}


class CourseResultOut(BaseModel):
    id: str
    course_id: str
    course_code: str
    course_name: str
    academic_term_id: str
    academic_term_name: str
    grade: str | None
    grade_points: float | None
    credits: int
    result_status: ResultStatus
    recorded_at: date

    model_config = {"from_attributes": True}


class MilestoneOut(BaseModel):
    id: str
    name: str
    academic_level: AcademicLevel
    description: str | None
    required_credits: int | None
    target_cgpa: float | None
    sequence_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class StudentMilestoneOut(BaseModel):
    id: str
    milestone_id: str
    milestone_name: str
    status: str
    completed_at: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}
