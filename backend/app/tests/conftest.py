from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.academic import AcademicTerm, Course, CoursePrerequisite
from app.models.enums import AcademicLevel, Severity, UserRole, RiskIndicatorType
from app.models.risk import RiskRule
from app.models.student import Student
from app.models.user import User
from app.services.policy_service import ensure_default_policies

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="function", autouse=True)
def db_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(db_session, email, role, full_name="Test User", password="Password123!"):
    user = User(email=email, password_hash=hash_password(password), full_name=full_name, role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_student(db_session, email, identifier, academic_level=AcademicLevel.foundation, assigned_staff_id=None, full_name="Student Test"):
    user = make_user(db_session, email, UserRole.student, full_name=full_name)
    student = Student(
        student_identifier=identifier, user_id=user.id, full_name=full_name, academic_level=academic_level,
        admission_date=date(2024, 1, 1), current_term="Sep 2026 Term", assigned_staff_id=assigned_staff_id,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return user, student


def login(client, email, password="Password123!"):
    response = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seeded_courses(db_session):
    term = AcademicTerm(name="Sep 2026 Term", start_date=date(2026, 9, 1), end_date=date(2027, 1, 15), is_active=True)
    db_session.add(term)
    course_a = Course(course_code="CS101", course_name="Intro to CS", credits=4, academic_level=AcademicLevel.foundation)
    course_b = Course(course_code="CS201", course_name="Advanced CS", credits=4, academic_level=AcademicLevel.foundation)
    db_session.add_all([course_a, course_b])
    db_session.flush()
    db_session.add(CoursePrerequisite(course_id=course_b.id, prerequisite_course_id=course_a.id, minimum_grade_points=4.0))
    db_session.commit()
    return {"term": term, "course_a": course_a, "course_b": course_b}


@pytest.fixture()
def default_policies(db_session):
    ensure_default_policies(db_session)
    return db_session
