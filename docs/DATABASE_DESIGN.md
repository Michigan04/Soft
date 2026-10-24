# Database Design

PostgreSQL schema for the IITM BS Student Risk Identification and Intervention Platform, implemented with SQLAlchemy 2.x models (`backend/app/models/`) and tracked with Alembic (`backend/alembic/`).

## Identifier strategy

Every table uses a UUID primary key. The column type is a custom `GUID` TypeDecorator (`backend/app/db/base.py`) that compiles to PostgreSQL's native `UUID` type in production and to `CHAR(36)` on other dialects. This was introduced so the automated test suite can run against SQLite without a live PostgreSQL instance, while production always uses Postgres's native UUID column — the application never changes behavior based on dialect beyond this column type.

## Timestamps

All `created_at` / `updated_at` columns are stored as timezone-aware UTC (`DateTime(timezone=True)` with Python `datetime.now(timezone.utc)` defaults).

## Entity overview

| Table | Purpose |
|---|---|
| `users` | Login identity + role (`student`, `faculty`, `ta`, `admin`) for every account. |
| `students` | One row per student, linked 1:1 to a `users` row. Holds current assigned staff, academic level, program status. |
| `academic_terms` | Terms (e.g. "Sep 2026 Term") with an `is_active` flag. |
| `courses` | Course catalog, scoped to an academic level. |
| `course_prerequisites` | Many-to-many prerequisite graph between courses, with a configurable `minimum_grade_points`. |
| `registrations` | A student's registration attempt for a course in a term. Unique on (student, course, term). Carries both a `status` (approved/rejected/...) and a `validation_status`. |
| `registration_validation_logs` | Append-only log of every validation request (US-02), used by the risk engine's "repeated registration failures" indicator. |
| `course_results` | Recorded grade/result per (student, course, term); unique per triple to prevent duplicate results. |
| `academic_milestones` / `student_milestones` | Program-level milestones (e.g. "Diploma Level Completion") and each student's progress against them. |
| `projects` | Capstone/qualifying project tracking (US-04). |
| `risk_rules` | Admin-configurable indicator rules: indicator type, threshold, severity, weight, optional academic-level scope (US-09). |
| `policy_settings` | Generic key/value policy store for values that aren't per-indicator rules: risk-score-to-level thresholds and CGPA projection assumptions. |
| `risk_assessments` / `risk_factors` | Immutable history of every risk assessment ever run, and the specific factors that contributed to each one. Never overwritten — a new assessment is always a new row. |
| `notifications` / `notification_deliveries` | In-app notification plus one delivery row per channel (in-app, email), so delivery status/attempts are tracked per channel. |
| `interventions` / `intervention_history` | Support activities logged by staff, with a full before/after change history (US-07). |
| `student_assignments` | Historical staff-assignment log; `students.assigned_staff_id` is the current pointer, this table is the full history (old rows get `is_active=false` + `unassigned_at` rather than being deleted). |
| `audit_logs` | Append-only log of sensitive actions (risk rule changes, assignments, imports, student/intervention updates). No API route can update or delete a row. |
| `data_imports` | One row per CSV import, including the validated-but-not-yet-committed row payload (`validated_rows` JSON) so validate and commit are separate steps. |

## Key constraints and indexes

- Unique constraints prevent duplicate `course_results` and `registrations` for the same (student, course, term).
- `risk_assessments` and `risk_factors` are insert-only from the application's perspective; there is no update/delete endpoint for either.
- Indexes are defined on frequently-filtered columns: `students.academic_level`, `students.assigned_staff_id`, `risk_assessments.risk_level`/`assessment_date`, `notifications.is_read`/`created_at`, `interventions.follow_up_date`, `audit_logs.action`/`entity_type`/`created_at`.
- Multi-row writes (e.g. CSV import commit, staff reassignment) run inside a transaction; CSV commit additionally uses a SQLAlchemy savepoint (`db.begin_nested()`) per row so one bad row cannot roll back rows that already succeeded.

## Migrations

The initial migration (`backend/alembic/versions/0001_initial_schema.py`) calls `Base.metadata.create_all`/`drop_all` from inside the Alembic revision rather than hand-written `op.create_table` calls or `alembic revision --autogenerate`. This is because autogeneration requires a live, reachable PostgreSQL instance, and neither Docker nor a working local PostgreSQL installation was available in the environment this project was built in (see `docs/ASSUMPTIONS.md`). Driving `create_all`/`drop_all` from a tracked migration still produces correct, dialect-specific PostgreSQL DDL (native enums, UUID columns, etc.) from the same models the application uses, and Alembic still tracks it as a normal revision. **Future schema changes should use `alembic revision --autogenerate --message "..."` against a running database** so subsequent migrations capture incremental diffs in the usual way; only this first migration uses the create_all shortcut.

## Seed data

`backend/app/db/seed.py` populates a complete, self-consistent demo dataset: 4 demo accounts (admin/faculty/faculty/TA) plus 12 synthetic students spread across Foundation/Diploma/Degree, deliberately tuned so the risk engine produces examples in all four risk categories (low/moderate/high/critical) plus one student with no academic records at all (to demonstrate explicit missing-data handling). See `docs/RISK_ENGINE.md` for exactly how those categories are produced.
