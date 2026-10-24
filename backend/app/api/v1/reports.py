from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.permissions import require_staff
from app.db.session import get_db
from app.models.enums import AcademicLevel
from app.models.user import User
from app.services.reporting_service import (
    intervention_outcomes,
    overdue_followups_report,
    progression_report,
    risk_trends,
    rows_to_csv,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/risk-trends")
def get_risk_trends(
    start_date: date | None = None, end_date: date | None = None, academic_level: AcademicLevel | None = None,
    export: bool = False, db: Session = Depends(get_db), current_user: User = Depends(require_staff),
):
    rows = risk_trends(db, start_date, end_date, academic_level)
    if export:
        return PlainTextResponse(rows_to_csv(rows), media_type="text/csv")
    return rows


@router.get("/intervention-outcomes")
def get_intervention_outcomes(
    start_date: date | None = None, end_date: date | None = None, staff_user_id: str | None = None,
    export: bool = False, db: Session = Depends(get_db), current_user: User = Depends(require_staff),
):
    rows = intervention_outcomes(db, start_date, end_date, staff_user_id)
    if export:
        return PlainTextResponse(rows_to_csv(rows), media_type="text/csv")
    return rows


@router.get("/progression")
def get_progression(
    academic_level: AcademicLevel | None = None, export: bool = False,
    db: Session = Depends(get_db), current_user: User = Depends(require_staff),
):
    rows = progression_report(db, academic_level)
    if export:
        return PlainTextResponse(rows_to_csv(rows), media_type="text/csv")
    return rows


@router.get("/overdue-followups")
def get_overdue_followups(
    export: bool = False, db: Session = Depends(get_db), current_user: User = Depends(require_staff)
):
    rows = overdue_followups_report(db)
    if export:
        return PlainTextResponse(rows_to_csv(rows), media_type="text/csv")
    return rows
