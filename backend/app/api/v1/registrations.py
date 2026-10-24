from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_accessible_student, get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.registration import Registration
from app.models.student import Student
from app.models.user import User
from app.schemas.registration import (
    RegistrationCreateRequest,
    RegistrationOut,
    RegistrationValidateRequest,
    RegistrationValidationResponse,
)
from app.services.registration_service import create_registrations, validate_registration

router = APIRouter(prefix="/registrations", tags=["registrations"])


def _check_student_access(db: Session, current_user: User, student_id: str) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if current_user.role == UserRole.student and student.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only register your own courses")
    if current_user.role in (UserRole.faculty, UserRole.ta) and student.assigned_staff_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This student is not assigned to you")
    return student


@router.post("/validate", response_model=RegistrationValidationResponse)
def validate(
    payload: RegistrationValidateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> RegistrationValidationResponse:
    student = _check_student_access(db, current_user, payload.student_id)
    result = validate_registration(db, student, payload.academic_term_id, payload.course_ids)
    return RegistrationValidationResponse(**result)


@router.post("", response_model=list[RegistrationOut], status_code=status.HTTP_201_CREATED)
def register(
    payload: RegistrationCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[RegistrationOut]:
    student = _check_student_access(db, current_user, payload.student_id)
    registrations = create_registrations(db, student, payload.academic_term_id, payload.course_ids)
    return [
        RegistrationOut(
            id=r.id, student_id=r.student_id, course_id=r.course_id, course_code=r.course.course_code,
            course_name=r.course.course_name, academic_term_id=r.academic_term_id, status=r.status,
            validation_status=r.validation_status, validation_errors=r.validation_errors,
        )
        for r in registrations
    ]


@router.get("", response_model=list[RegistrationOut])
def list_registrations(
    student_id: str | None = None,
    academic_term_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RegistrationOut]:
    query = select(Registration)
    if student_id:
        _check_student_access(db, current_user, student_id)
        query = query.where(Registration.student_id == student_id)
    elif current_user.role == UserRole.student:
        student = db.execute(select(Student).where(Student.user_id == current_user.id)).scalar_one_or_none()
        if student is None:
            return []
        query = query.where(Registration.student_id == student.id)
    elif current_user.role in (UserRole.faculty, UserRole.ta):
        query = query.join(Student).where(Student.assigned_staff_id == current_user.id)

    if academic_term_id:
        query = query.where(Registration.academic_term_id == academic_term_id)

    registrations = db.execute(query).scalars().all()
    return [
        RegistrationOut(
            id=r.id, student_id=r.student_id, course_id=r.course_id, course_code=r.course.course_code,
            course_name=r.course.course_name, academic_term_id=r.academic_term_id, status=r.status,
            validation_status=r.validation_status, validation_errors=r.validation_errors,
        )
        for r in registrations
    ]
