from app.models.enums import ResultStatus
from app.models.result import CourseResult
from app.services.cgpa_service import compute_cgpa, project_target_cgpa_scenarios
from app.tests.conftest import make_student


def test_cgpa_computation_credit_weighted(db_session, seeded_courses):
    _user, student = make_student(db_session, "cgpa1@test.dev", "CGPA1")
    db_session.add_all([
        CourseResult(student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
                     grade="A", grade_points=8, credits=4, result_status=ResultStatus.pass_),
        CourseResult(student_id=student.id, course_id=seeded_courses["course_b"].id, academic_term_id=seeded_courses["term"].id,
                     grade="B", grade_points=6, credits=4, result_status=ResultStatus.pass_),
    ])
    db_session.commit()

    cgpa, completed_credits, attempted_credits = compute_cgpa(db_session, student.id)
    assert cgpa == 7.0  # (8*4 + 6*4) / 8
    assert completed_credits == 8
    assert attempted_credits == 8


def test_cgpa_excludes_incomplete_results_from_grade_calc(db_session, seeded_courses):
    _user, student = make_student(db_session, "cgpa2@test.dev", "CGPA2")
    db_session.add_all([
        CourseResult(student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
                     grade="A", grade_points=8, credits=4, result_status=ResultStatus.pass_),
        CourseResult(student_id=student.id, course_id=seeded_courses["course_b"].id, academic_term_id=seeded_courses["term"].id,
                     grade=None, grade_points=None, credits=4, result_status=ResultStatus.incomplete),
    ])
    db_session.commit()

    cgpa, completed_credits, attempted_credits = compute_cgpa(db_session, student.id)
    assert cgpa == 8.0
    assert completed_credits == 4
    assert attempted_credits == 8


def test_no_results_returns_none_cgpa_not_zero(db_session):
    _user, student = make_student(db_session, "cgpa3@test.dev", "CGPA3")
    cgpa, completed_credits, attempted_credits = compute_cgpa(db_session, student.id)
    assert cgpa is None
    assert completed_credits == 0


def test_target_cgpa_scenarios_labelled_as_assumptions(db_session, default_policies, seeded_courses):
    _user, student = make_student(db_session, "cgpa4@test.dev", "CGPA4")
    db_session.add(CourseResult(
        student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
        grade="B", grade_points=6, credits=4, result_status=ResultStatus.pass_,
    ))
    db_session.commit()

    scenarios = project_target_cgpa_scenarios(db_session, student.id, remaining_credits=8, targets=[7.0, 9.9])
    assert len(scenarios) == 2
    high_target = [s for s in scenarios if s["target_cgpa"] == 9.9][0]
    assert high_target["feasible"] is False
    assert "not realistically achievable" in high_target["note"]
