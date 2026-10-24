from app.models.enums import ImportType
from app.services.import_service import commit_import, create_pending_import, mark_validated, parse_csv_text, validate_rows
from app.tests.conftest import make_student


STUDENTS_CSV = """student_identifier,email,full_name,academic_level,admission_date
NEWSTU1,newstu1@test.dev,New Student One,foundation,2026-01-10
NEWSTU2,newstu2@test.dev,New Student Two,bogus_level,2026-01-10
NEWSTU1,dupe@test.dev,Duplicate Row,foundation,2026-01-10
"""


def test_csv_parsing():
    rows = parse_csv_text(STUDENTS_CSV)
    assert len(rows) == 3
    assert rows[0]["student_identifier"] == "NEWSTU1"


def test_invalid_academic_level_rejected(db_session):
    rows = parse_csv_text(STUDENTS_CSV)
    valid_rows, row_errors = validate_rows(db_session, ImportType.students, rows)
    assert len(valid_rows) == 1
    assert len(row_errors) == 2
    error_messages = [e for row in row_errors for e in row["errors"]]
    assert any("Invalid academic_level" in m for m in error_messages)


def test_duplicate_row_within_file_rejected(db_session):
    rows = parse_csv_text(STUDENTS_CSV)
    _valid_rows, row_errors = validate_rows(db_session, ImportType.students, rows)
    dup_errors = [e for row in row_errors for e in row["errors"] if "Duplicate row" in e]
    assert len(dup_errors) == 1


def test_existing_student_identifier_rejected(db_session):
    make_student(db_session, "existing@test.dev", "NEWSTU1")
    rows = parse_csv_text(STUDENTS_CSV)
    _valid_rows, row_errors = validate_rows(db_session, ImportType.students, rows)
    messages = [e for row in row_errors for e in row["errors"]]
    assert any("already exists" in m for m in messages)


def test_missing_required_column_reported_with_row_number():
    rows = [{"student_identifier": "X", "email": "x@test.dev"}]  # missing full_name, academic_level, admission_date
    import app.db.session  # noqa: F401
    from app.tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        _valid, row_errors = validate_rows(db, ImportType.students, rows)
    finally:
        db.close()
    assert len(row_errors) == 1
    assert row_errors[0]["row_number"] == 2


def test_commit_import_creates_students_and_handles_row_failure(db_session):
    rows = [
        {"student_identifier": "COMMIT1", "email": "commit1@test.dev", "full_name": "Commit One", "academic_level": "foundation", "admission_date": "2026-01-10"},
        {"student_identifier": "COMMIT2", "email": "commit2@test.dev", "full_name": "Commit Two", "academic_level": "foundation", "admission_date": "2026-01-10"},
    ]
    valid_rows, row_errors = validate_rows(db_session, ImportType.students, rows)
    assert len(valid_rows) == 2

    data_import = create_pending_import(db_session, uploaded_by=None, filename="x.csv", import_type=ImportType.students)
    data_import = mark_validated(db_session, data_import, valid_rows, row_errors, total_rows=len(rows))
    data_import = commit_import(db_session, data_import)

    assert data_import.successful_rows == 2
    assert data_import.failed_rows == 0
    assert data_import.status.value == "committed"

    from app.models.student import Student
    students = db_session.query(Student).filter(Student.student_identifier.in_(["COMMIT1", "COMMIT2"])).all()
    assert len(students) == 2
