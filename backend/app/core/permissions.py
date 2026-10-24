from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.student import Student
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return dependency


require_admin = require_roles(UserRole.admin)
require_staff = require_roles(UserRole.admin, UserRole.faculty, UserRole.ta)
require_any_role = require_roles(UserRole.admin, UserRole.faculty, UserRole.ta, UserRole.student)


def get_accessible_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Student:
    """Fetch a student record while enforcing ownership/assignment rules.

    - Students may only access their own record.
    - Faculty/TA may only access students currently assigned to them.
    - Admins may access any student.
    """
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if current_user.role == UserRole.admin:
        return student

    if current_user.role == UserRole.student:
        if student.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own records")
        return student

    if current_user.role in (UserRole.faculty, UserRole.ta):
        if student.assigned_staff_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This student is not currently assigned to you",
            )
        return student

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
