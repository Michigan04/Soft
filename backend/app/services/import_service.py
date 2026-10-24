"""CSV import validation and commit logic for US-10.

Flow: `validate_csv` parses + validates a CSV and stores the validated rows on a
`DataImport` record (status=validated). `commit_import` then re-reads that same
record and writes the rows to the database inside per-row transactions, so a
single bad row cannot corrupt rows that already succeeded.
"""

import csv
import io
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.academic import AcademicTerm, Course
from app.models.data_import import DataImport
from app.models.enums import (
    AcademicLevel,
    ImportStatus,
    ImportType,
    ProjectStatus,
    RegistrationStatus,
    ResultStatus,
    ValidationStatus,
)
from app.models.project import Project
from app.models.registration import Registration
from app.models.result import CourseResult
from app.models.student import Student
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password

REQUIRED_COLUMNS: dict[ImportType, list[str]] = {
    ImportType.students: ["student_identifier", "email", "full_name", "academic_level", "admission_date"],
    ImportType.course_results: [
        "student_identifier", "course_code", "academic_term_name", "result_status", "credits",
    ],
    ImportType.registrations: ["student_identifier", "course_code", "academic_term_name", "status"],
    ImportType.projects: ["student_identifier", "title", "status"],
}


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def parse_csv_text(content: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content))
    return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def validate_rows(db: Session, import_type: ImportType, rows: list[dict]) -> tuple[list[dict], list[dict]]:
    required = REQUIRED_COLUMNS[import_type]
    valid_rows: list[dict] = []
    row_errors: list[dict] = []
    seen_keys: set[tuple] = set()

    for idx, row in enumerate(rows, start=2):  # row 1 is the header
        errors: list[str] = []
        for col in required:
            if not row.get(col):
                errors.append(f"Missing required value for '{col}'.")

        if errors:
            row_errors.append({"row_number": idx, "errors": errors})
            continue

        if import_type == ImportType.students:
            if row["academic_level"] not in {lvl.value for lvl in AcademicLevel}:
                errors.append(f"Invalid academic_level '{row['academic_level']}'.")
            if _parse_date(row["admission_date"]) is None:
                errors.append("admission_date must be in YYYY-MM-DD format.")
            existing = db.query(Student).filter(Student.student_identifier == row["student_identifier"]).one_or_none()
            if existing:
                errors.append(f"student_identifier '{row['student_identifier']}' already exists.")
            key = ("student", row["student_identifier"])

        elif import_type == ImportType.course_results:
            student = db.query(Student).filter(Student.student_identifier == row["student_identifier"]).one_or_none()
            course = db.query(Course).filter(Course.course_code == row["course_code"]).one_or_none()
            term = db.query(AcademicTerm).filter(AcademicTerm.name == row["academic_term_name"]).one_or_none()
            if student is None:
                errors.append(f"Unknown student_identifier '{row['student_identifier']}'.")
            if course is None:
                errors.append(f"Unknown course_code '{row['course_code']}'.")
            if term is None:
                errors.append(f"Unknown academic_term_name '{row['academic_term_name']}'.")
            if row["result_status"] not in {s.value for s in ResultStatus}:
                errors.append(f"Invalid result_status '{row['result_status']}'.")
            try:
                int(row["credits"])
            except ValueError:
                errors.append("credits must be an integer.")
            if row.get("grade_points"):
                try:
                    float(row["grade_points"])
                except ValueError:
                    errors.append("grade_points must be numeric.")
            key = ("result", row["student_identifier"], row["course_code"], row["academic_term_name"])
            if student and course and term:
                dup = db.query(CourseResult).filter(
                    CourseResult.student_id == student.id,
                    CourseResult.course_id == course.id,
                    CourseResult.academic_term_id == term.id,
                ).one_or_none()
                if dup:
                    errors.append("A result for this student/course/term already exists.")

        elif import_type == ImportType.registrations:
            student = db.query(Student).filter(Student.student_identifier == row["student_identifier"]).one_or_none()
            course = db.query(Course).filter(Course.course_code == row["course_code"]).one_or_none()
            term = db.query(AcademicTerm).filter(AcademicTerm.name == row["academic_term_name"]).one_or_none()
            if student is None:
                errors.append(f"Unknown student_identifier '{row['student_identifier']}'.")
            if course is None:
                errors.append(f"Unknown course_code '{row['course_code']}'.")
            if term is None:
                errors.append(f"Unknown academic_term_name '{row['academic_term_name']}'.")
            if row["status"] not in {s.value for s in RegistrationStatus}:
                errors.append(f"Invalid status '{row['status']}'.")
            key = ("registration", row["student_identifier"], row["course_code"], row["academic_term_name"])

        elif import_type == ImportType.projects:
            student = db.query(Student).filter(Student.student_identifier == row["student_identifier"]).one_or_none()
            if student is None:
                errors.append(f"Unknown student_identifier '{row['student_identifier']}'.")
            if row["status"] not in {s.value for s in ProjectStatus}:
                errors.append(f"Invalid status '{row['status']}'.")
            for date_col in ("start_date", "due_date", "completion_date"):
                if row.get(date_col) and _parse_date(row[date_col]) is None:
                    errors.append(f"{date_col} must be in YYYY-MM-DD format.")
            key = ("project", row["student_identifier"], row["title"])

        if key in seen_keys:
            errors.append("Duplicate row within this file.")
        seen_keys.add(key)

        if errors:
            row_errors.append({"row_number": idx, "errors": errors})
        else:
            valid_rows.append(row)

    return valid_rows, row_errors


def create_pending_import(db: Session, uploaded_by: str, filename: str, import_type: ImportType) -> DataImport:
    data_import = DataImport(
        uploaded_by=uploaded_by, filename=filename, import_type=import_type, status=ImportStatus.pending
    )
    db.add(data_import)
    db.commit()
    db.refresh(data_import)
    return data_import


def mark_validated(db: Session, data_import: DataImport, valid_rows: list[dict], row_errors: list[dict], total_rows: int) -> DataImport:
    data_import.status = ImportStatus.validated
    data_import.total_rows = total_rows
    data_import.validated_rows = valid_rows
    data_import.row_errors = row_errors
    data_import.failed_rows = len(row_errors)
    db.commit()
    db.refresh(data_import)
    return data_import


def commit_import(db: Session, data_import: DataImport) -> DataImport:
    from app.db.base import utcnow

    if data_import.status != ImportStatus.validated or not data_import.validated_rows:
        raise ValueError("Import has not been validated, or has no valid rows to commit.")

    successful = 0
    failed = 0
    commit_errors: list[dict] = []

    for idx, row in enumerate(data_import.validated_rows, start=1):
        savepoint = db.begin_nested()
        try:
            if data_import.import_type == ImportType.students:
                user = User(
                    email=row["email"],
                    password_hash=hash_password(row.get("password") or "ChangeMe123!"),
                    full_name=row["full_name"],
                    role=UserRole.student,
                )
                db.add(user)
                db.flush()
                student = Student(
                    student_identifier=row["student_identifier"],
                    user_id=user.id,
                    full_name=row["full_name"],
                    academic_level=AcademicLevel(row["academic_level"]),
                    admission_date=_parse_date(row["admission_date"]),
                    current_term=row.get("current_term") or None,
                )
                db.add(student)

            elif data_import.import_type == ImportType.course_results:
                student = db.query(Student).filter(Student.student_identifier == row["student_identifier"]).one()
                course = db.query(Course).filter(Course.course_code == row["course_code"]).one()
                term = db.query(AcademicTerm).filter(AcademicTerm.name == row["academic_term_name"]).one()
                result_status = ResultStatus(row["result_status"])
                course_result = CourseResult(
                    student_id=student.id,
                    course_id=course.id,
                    academic_term_id=term.id,
                    grade=row.get("grade") or None,
                    grade_points=float(row["grade_points"]) if row.get("grade_points") else None,
                    credits=int(row["credits"]),
                    result_status=result_status,
                    recorded_at=utcnow(),
                )
                db.add(course_result)
                db.flush()
                if result_status == ResultStatus.fail:
                    from app.services.notification_service import notify_failed_result

                    notify_failed_result(db, course_result)

            elif data_import.import_type == ImportType.registrations:
                student = db.query(Student).filter(Student.student_identifier == row["student_identifier"]).one()
                course = db.query(Course).filter(Course.course_code == row["course_code"]).one()
                term = db.query(AcademicTerm).filter(AcademicTerm.name == row["academic_term_name"]).one()
                db.add(
                    Registration(
                        student_id=student.id,
                        course_id=course.id,
                        academic_term_id=term.id,
                        status=RegistrationStatus(row["status"]),
                        validation_status=ValidationStatus.not_validated,
                    )
                )

            elif data_import.import_type == ImportType.projects:
                student = db.query(Student).filter(Student.student_identifier == row["student_identifier"]).one()
                db.add(
                    Project(
                        student_id=student.id,
                        title=row["title"],
                        description=row.get("description") or None,
                        status=ProjectStatus(row["status"]),
                        start_date=_parse_date(row["start_date"]) if row.get("start_date") else None,
                        due_date=_parse_date(row["due_date"]) if row.get("due_date") else None,
                        completion_date=_parse_date(row["completion_date"]) if row.get("completion_date") else None,
                        grade=row.get("grade") or None,
                    )
                )

            savepoint.commit()
            successful += 1
        except Exception as exc:  # noqa: BLE001 - row-level isolation by design
            savepoint.rollback()
            failed += 1
            commit_errors.append({"row_number": idx, "errors": [str(exc)]})

    data_import.status = ImportStatus.committed
    data_import.successful_rows = successful
    data_import.failed_rows = data_import.failed_rows + failed
    data_import.completed_at = utcnow()
    if commit_errors:
        data_import.row_errors = (data_import.row_errors or []) + commit_errors
    db.commit()
    db.refresh(data_import)
    return data_import
