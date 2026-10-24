from datetime import datetime

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    staff_user_id: str


class AssignmentOut(BaseModel):
    id: str
    student_id: str
    staff_user_id: str
    assigned_by: str | None
    assigned_at: datetime
    unassigned_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class StaffWorkloadOut(BaseModel):
    staff_user_id: str
    staff_name: str
    role: str
    assigned_student_count: int
    open_interventions: int
    overdue_followups: int
