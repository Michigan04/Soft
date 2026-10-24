from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_students: int
    at_risk_students: int
    high_risk_students: int
    critical_risk_students: int
    pending_interventions: int
    overdue_followups: int
    unread_notifications: int


class RiskDistributionItem(BaseModel):
    risk_level: str
    count: int


class ProgressionTrendPoint(BaseModel):
    period: str
    average_cgpa: float | None
    at_risk_count: int
    total_students: int
