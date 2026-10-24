from app.models.enums import ResultStatus
from app.models.result import CourseResult
from app.services.registration_service import create_registrations, validate_registration
from app.tests.conftest import make_student


def test_missing_prerequisite_is_rejected(db_session, seeded_courses):
    _user, student = make_student(db_session, "reg1@test.dev", "REG1")
    result = validate_registration(db_session, student, seeded_courses["term"].id, [seeded_courses["course_b"].id])
    assert result["overall_valid"] is False
    assert any("Missing prerequisite" in e for e in result["results"][0]["errors"])


def test_passed_prerequisite_allows_registration(db_session, seeded_courses):
    _user, student = make_student(db_session, "reg2@test.dev", "REG2")
    db_session.add(CourseResult(
        student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
        grade="A", grade_points=8, credits=4, result_status=ResultStatus.pass_,
    ))
    db_session.commit()

    result = validate_registration(db_session, student, seeded_courses["term"].id, [seeded_courses["course_b"].id])
    assert result["overall_valid"] is True


def test_insufficient_prerequisite_grade_is_rejected(db_session, seeded_courses):
    _user, student = make_student(db_session, "reg3@test.dev", "REG3")
    db_session.add(CourseResult(
        student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
        grade="D", grade_points=2, credits=4, result_status=ResultStatus.pass_,
    ))
    db_session.commit()

    result = validate_registration(db_session, student, seeded_courses["term"].id, [seeded_courses["course_b"].id])
    assert result["overall_valid"] is False
    assert any("below required minimum" in e for e in result["results"][0]["errors"])


def test_invalid_registration_is_persisted_as_rejected_not_approved(db_session, seeded_courses):
    _user, student = make_student(db_session, "reg4@test.dev", "REG4")
    registrations = create_registrations(db_session, student, seeded_courses["term"].id, [seeded_courses["course_b"].id])
    assert len(registrations) == 1
    assert registrations[0].status.value == "rejected"
    assert registrations[0].validation_status.value == "invalid"


def test_duplicate_course_selection_in_same_request_is_flagged(db_session, seeded_courses):
    _user, student = make_student(db_session, "reg5@test.dev", "REG5")
    result = validate_registration(
        db_session, student, seeded_courses["term"].id, [seeded_courses["course_a"].id, seeded_courses["course_a"].id]
    )
    errors = result["results"][0]["errors"] + result["results"][1]["errors"]
    assert any("more than once" in e for e in errors)
