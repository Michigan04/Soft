# Assumptions, Trade-offs, and Known Limitations

This file collects every deliberate simplification or engineering judgment call made while building this project, so they're never mistaken for official IITM policy or for oversights.

## Environment constraints that shaped the build

This project was built in a sandbox with **no Docker** and **no working local PostgreSQL** (the only local PostgreSQL install present was missing its `lib` directory and could not run `initdb`). Two decisions follow directly from this:

1. **Portable UUID column type.** All primary/foreign keys use a custom `GUID` TypeDecorator (`backend/app/db/base.py`) instead of `sqlalchemy.dialects.postgresql.UUID` directly. It compiles to Postgres's native `UUID` type in production and to `CHAR(36)` elsewhere. This let the automated pytest suite run against SQLite in this environment while keeping correct native-UUID behavior on Postgres — it is not a workaround visible to any API consumer.
2. **Initial Alembic migration uses `create_all`/`drop_all`.** `alembic revision --autogenerate` needs a live database connection to diff against, which wasn't available. The single initial migration instead calls `Base.metadata.create_all`/`drop_all` against whatever database Alembic is pointed at, producing correct Postgres DDL from the same models the app uses. It was validated by running `alembic upgrade head` against a scratch SQLite database (not Postgres) and confirming all 21 tables were created with the expected relationships. **You must verify this migration against a real PostgreSQL database before relying on it in production**, and all schema changes after this first migration should use normal `--autogenerate`.

**You will need Docker (for `docker-compose up -d` → PostgreSQL) or your own working PostgreSQL instance to run this project as intended.** See `README.md` for setup steps.

## Risk engine assumptions

- Severity → points mapping (`info=5, warning=15, critical=30`) and the default risk-level cutoffs (`moderate>=25, high>=50, critical>=75` out of 100) are our own defaults, not derived from any IITM policy. Both are admin-configurable at runtime (Rules & Academic Policies page / `policy_settings` table).
- When multiple rules share an indicator type and more than one triggers, only the highest-scoring one counts, to avoid double-counting one underlying issue (see `docs/RISK_ENGINE.md`).
- This is a rule-based system, not a trained/validated predictive model. It must not be presented to stakeholders as predicting dropout with any measured accuracy.

## CGPA / academic assumptions

- CGPA is credit-weighted across all `course_results` with a non-null `grade_points` and status `pass` or `fail`; `incomplete`/`withdrawn` results are excluded from the GPA calculation but still counted toward "attempted credits" for transparency.
- The grade-point scale (`max_grade_points`, default 10) and default course credit count are stored as an editable `policy_settings` row (`cgpa_assumptions`), not hardcoded, and every CGPA/target-CGPA response in the API explicitly labels these as assumptions (see `assumptions` field on `GET /students/{id}/cgpa-summary`).
- Target-CGPA projections assume all remaining credits are graded at one uniform average grade — they do not model course-by-course variation. This is stated in the API response itself, not just in documentation.
- No official IITM grading rubric, prerequisite policy, or milestone credit requirement is encoded here — all course/milestone/prerequisite data is synthetic seed data for demonstration, and real deployment would need real academic policy data loaded via the CSV import pipeline or direct seeding.

## Email / notifications

- SMTP is optional. When `SMTP_HOST` is unset, `backend/app/services/notification_service.py` logs the email to the `notifications` logger instead of sending it ("dev/console email backend") — this is intentional so the whole application is demoable without any live mail server, and is called out in the README.
- Notification de-duplication uses a `dedupe_key` column; a second notification with the same key is silently skipped rather than creating a duplicate row.

## Backend architecture

- No separate `repositories/` layer was implemented; services call SQLAlchemy directly. For this project's scope, an additional repository abstraction over SQLAlchemy's Session/Query API would have added indirection without a corresponding benefit — the services module boundary already separates business logic from API routing.
- `GET /students` computes risk/CGPA/follow-up fields in Python after fetching candidate rows, rather than as pure SQL aggregates, so that filtering/sorting by derived fields (risk score, pending follow-ups) stays correct without duplicating the risk-engine's logic in SQL. This is fine at the seed-data scale (dozens–low hundreds of students) but would need to move to materialized/denormalized columns or a background job at real program scale (thousands of students).
- CSV import row-level isolation uses SQLAlchemy savepoints (`db.begin_nested()`) per row inside one outer transaction, rather than one transaction per row, so a partial failure can't leave the `data_imports` summary counts inconsistent with what was actually committed.

## Frontend design

- The reference screenshot (`image.png`) is the real IITM BS student dashboard: a white header with the institute crest, a narrow dark icon rail on the left, and maroon/brick-red content cards on a light-gray background. This palette (maroon primary `#8c1d2b`, near-black sidebar `#16182b`, light-gray page background) and the overall white-header/dark-sidebar/card layout were carried over directly.
- The reference's sidebar is icon-only with no visible labels. This application has ~11 distinct destinations across 4 roles, several with similar-enough purposes (e.g. "Students" vs "Staff Assignments" vs "Reports") that icon-only navigation without a label would hurt usability. The sidebar here keeps the same dark background and maroon active-state styling but shows text labels, which is called out here as a deliberate, usability-motivated deviation from the reference rather than an oversight.
- Charts (Chart.js via vue-chartjs) use a small fixed palette matching the risk badge colors (low=green, moderate=amber, high=orange, critical=red) so a risk level reads the same color everywhere in the app.

## Demo data and accounts

- All student names and records are synthetic (seed script explicitly fixes a random seed for reproducibility). No real student data is used anywhere.
- Demo accounts and the shared demo password are only intended for local development; `ENABLE_DEMO_ACCOUNTS` exists as a flag in `.env.example` to make this explicit, and the README states demo credentials must never be used in a production deployment.

## Testing

- The backend pytest suite (`backend/app/tests/`) runs against an in-memory SQLite database via dependency override, independent of whatever `DATABASE_URL` is configured for the real app — this is what let the full suite (43 tests) execute and pass in this sandbox without PostgreSQL.
- Frontend testing is intentionally lighter than the backend's: 18 Vitest unit tests cover pure logic and simple components (risk color/label mapping, the API error-message helper, auth-store role getters, pagination button states/events) rather than full page-level integration tests, given the scope of this build. The frontend was additionally verified by building it (`npm run build`, zero errors) and by exercising the live API it calls end-to-end over HTTP (login, RBAC, dashboard, students list, notifications) with both dev servers running simultaneously.
