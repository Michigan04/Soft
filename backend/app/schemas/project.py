from datetime import date

from pydantic import BaseModel

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    student_id: str
    title: str
    description: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    supervisor_id: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    due_date: date | None = None
    completion_date: date | None = None
    grade: str | None = None
    supervisor_id: str | None = None


class ProjectOut(BaseModel):
    id: str
    student_id: str
    title: str
    description: str | None
    status: ProjectStatus
    start_date: date | None
    due_date: date | None
    completion_date: date | None
    grade: str | None
    supervisor_id: str | None
    supervisor_name: str | None = None

    model_config = {"from_attributes": True}


class CgpaSummary(BaseModel):
    current_cgpa: float | None
    completed_credits: int
    total_attempted_credits: int
    pending_requirements: list[str]
    target_scenarios: list["TargetScenario"]
    assumptions: list[str]


class TargetScenario(BaseModel):
    target_cgpa: float
    remaining_credits: int
    required_avg_grade_points: float | None
    feasible: bool
    note: str
