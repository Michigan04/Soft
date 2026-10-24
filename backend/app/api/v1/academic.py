from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.db.session import get_db
from app.models.academic import AcademicTerm, Course
from app.models.enums import AcademicLevel
from app.models.user import User
from app.schemas.academic import AcademicTermOut, CourseOut

router = APIRouter(tags=["academic"])


@router.get("/academic-terms", response_model=list[AcademicTermOut])
def list_terms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[AcademicTerm]:
    return db.execute(select(AcademicTerm).order_by(AcademicTerm.start_date.desc())).scalars().all()


@router.get("/courses", response_model=list[CourseOut])
def list_courses(
    academic_level: AcademicLevel | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Course]:
    query = select(Course).where(Course.is_active.is_(True))
    if academic_level:
        query = query.where(Course.academic_level == academic_level)
    return db.execute(query.order_by(Course.course_code)).scalars().all()
