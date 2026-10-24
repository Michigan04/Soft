from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import InterventionOutcome, InterventionStatus, InterventionType


class InterventionCreate(BaseModel):
    student_id: str
    intervention_type: InterventionType
    description: str
    follow_up_date: date | None = None


class InterventionUpdate(BaseModel):
    status: InterventionStatus | None = None
    outcome: InterventionOutcome | None = None
    description: str | None = None
    follow_up_date: date | None = None


class InterventionHistoryOut(BaseModel):
    changed_at: datetime
    field_changed: str
    old_value: str | None
    new_value: str | None

    model_config = {"from_attributes": True}


class InterventionOut(BaseModel):
    id: str
    student_id: str
    staff_user_id: str
    staff_user_name: str | None = None
    intervention_type: InterventionType
    description: str
    status: InterventionStatus
    outcome: InterventionOutcome | None
    follow_up_date: date | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    history: list[InterventionHistoryOut] = []

    model_config = {"from_attributes": True}
