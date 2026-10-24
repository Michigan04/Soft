from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import AcademicTerm, Course, CoursePrerequisite
from app.models.enums import RegistrationStatus, ResultStatus, ValidationStatus
from app.models.registration import Registration, RegistrationValidationLog
from app.models.result import CourseResult
from app.models.student import Student


def validate_registration(
    db: Session, student: Student, academic_term_id: str, course_ids: list[str]
) -> dict:
    term = db.get(AcademicTerm, academic_term_id)
    results = []
    overall_valid = True

    existing_registrations = db.execute(
        select(Registration).where(
            Registration.student_id == student.id,
            Registration.academic_term_id == academic_term_id,
            Registration.status != RegistrationStatus.cancelled,
        )
    ).scalars().all()
    already_registered_course_ids = {r.course_id for r in existing_registrations}

    for course_id in course_ids:
        errors: list[str] = []
        course = db.get(Course, course_id)

        if term is None:
            errors.append("Academic term not found.")
        if course is None:
            errors.append("Course not found.")
            results.append(
                {"course_id": course_id, "course_code": "UNKNOWN", "course_name": "Unknown course",
                 "is_valid": False, "errors": errors}
            )
            overall_valid = False
            continue

        if not course.is_active:
            errors.append(f"{course.course_code} is not currently offered.")

        if course.academic_level != student.academic_level:
            errors.append(
                f"{course.course_code} belongs to the {course.academic_level.value} level; "
                f"student is in {student.academic_level.value}."
            )

        if course_id in already_registered_course_ids:
            errors.append(f"Already registered for {course.course_code} in this term.")

        if course_id in course_ids and course_ids.count(course_id) > 1:
            errors.append(f"{course.course_code} was selected more than once in this request.")

        prereqs = db.execute(
            select(CoursePrerequisite).where(CoursePrerequisite.course_id == course_id)
        ).scalars().all()
        for prereq in prereqs:
            best_result = db.execute(
                select(CourseResult)
                .where(
                    CourseResult.student_id == student.id,
                    CourseResult.course_id == prereq.prerequisite_course_id,
                    CourseResult.result_status == ResultStatus.pass_,
                )
                .order_by(CourseResult.grade_points.desc())
                .limit(1)
            ).scalar_one_or_none()
            prereq_course = db.get(Course, prereq.prerequisite_course_id)
            prereq_code = prereq_course.course_code if prereq_course else prereq.prerequisite_course_id
            if best_result is None:
                errors.append(f"Missing prerequisite: {prereq_code} has not been passed.")
            elif best_result.grade_points is not None and float(best_result.grade_points) < float(prereq.minimum_grade_points):
                errors.append(
                    f"Prerequisite {prereq_code} grade points ({best_result.grade_points}) below required "
                    f"minimum ({prereq.minimum_grade_points})."
                )

        is_valid = len(errors) == 0
        if not is_valid:
            overall_valid = False

        results.append(
            {
                "course_id": course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "is_valid": is_valid,
                "errors": errors,
            }
        )

    validation_result = {"overall_valid": overall_valid, "results": results}

    db.add(
        RegistrationValidationLog(
            student_id=student.id,
            academic_term_id=academic_term_id,
            requested_courses=course_ids,
            validation_result=validation_result,
        )
    )
    db.commit()

    return {"student_id": student.id, "academic_term_id": academic_term_id, "overall_valid": overall_valid, "results": results}


def create_registrations(db: Session, student: Student, academic_term_id: str, course_ids: list[str]) -> list[Registration]:
    """Validates then persists registration attempts. Invalid selections are
    stored with status=rejected so they can never be mistaken for approved
    registrations (US-02)."""
    validation = validate_registration(db, student, academic_term_id, course_ids)
    created: list[Registration] = []

    for course_result in validation["results"]:
        if course_result["course_code"] == "UNKNOWN":
            continue
        existing = db.execute(
            select(Registration).where(
                Registration.student_id == student.id,
                Registration.course_id == course_result["course_id"],
                Registration.academic_term_id == academic_term_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue

        registration = Registration(
            student_id=student.id,
            course_id=course_result["course_id"],
            academic_term_id=academic_term_id,
            status=RegistrationStatus.approved if course_result["is_valid"] else RegistrationStatus.rejected,
            validation_status=ValidationStatus.valid if course_result["is_valid"] else ValidationStatus.invalid,
            validation_errors=course_result["errors"] or None,
        )
        db.add(registration)
        created.append(registration)

    db.commit()
    for r in created:
        db.refresh(r)
    return created
