# API Guide

Base path: `/api/v1`. Interactive Swagger UI: `http://localhost:8000/docs`. Raw OpenAPI schema: `http://localhost:8000/openapi.json`.

## Authentication

- `POST /api/v1/auth/login` — OAuth2 password flow (`application/x-www-form-urlencoded`, fields `username`/`password`, `username` is the user's email). Returns a JWT `access_token`.
- `GET /api/v1/auth/me` — current user (id, email, full_name, role, and `student_id` if the account is a student).
- All other endpoints require `Authorization: Bearer <token>`.

## Roles

`student`, `faculty`, `ta`, `admin`. Enforcement happens **in the backend** via FastAPI dependencies (`app/core/permissions.py`) — `require_roles(...)` for role checks, and `get_accessible_student` for per-student ownership checks (a student can only access their own record; faculty/TA only students currently assigned to them; admin can access any student). The frontend also hides/redirects UI the role can't use, but this is a usability layer only — every sensitive check is re-verified server-side.

## Endpoint groups

| Group | Base path | Notes |
|---|---|---|
| Auth | `/auth` | login, me |
| Dashboard | `/dashboard` | summary, risk-distribution, progression-trends — all scoped to the caller's visible students (faculty/TA see only their assigned students) |
| Reference data | `/academic-terms`, `/courses` | read-only lookups used by registration/import forms |
| Students | `/students` | list/create/detail/update + sub-resources: academic-history, risk-assessments, assess-risk, interventions, milestones, projects, cgpa-summary, notifications |
| Registrations | `/registrations` | validate, create (US-02) |
| Projects / Milestones | `/projects`, `/milestones` | CRUD + listing |
| Interventions | `/interventions` | create/update/list, with `overdue_only` filter |
| Assignments | `/students/{id}/assignments`, `/staff/workload` | admin-only |
| Notifications | `/notifications` | caller's own notifications only |
| Rules | `/rules`, `/rules/policies` | admin-only; risk rule CRUD + policy key/value settings |
| Imports | `/imports/validate`, `/imports/commit`, `/imports` | admin-only CSV import pipeline |
| Audit | `/audit-logs` | admin-only, read-only (no update/delete route exists) |
| Reports | `/reports/*` | risk-trends, progression, intervention-outcomes, overdue-followups; any of them returns CSV when called with `?export=true` |

## Pagination

List endpoints that can grow large (`/students`, `/audit-logs`) return:
```json
{ "items": [...], "total": 42, "page": 1, "page_size": 20, "pages": 3 }
```

## Error format

FastAPI's standard `{"detail": "..."}` (or a list of field errors for validation failures) on non-2xx responses. The frontend's `apiErrorMessage()` helper renders either shape.

## CSV import flow (US-10)

1. `POST /imports/validate` (multipart: `import_type`, `file`) — parses and validates every row, returns a per-row error report plus a `validation_token` (the `data_imports.id` for this attempt) and a preview of the first 10 valid rows. Nothing is written to the target tables yet.
2. `POST /imports/commit` (`{"validation_token": "..."}`) — re-reads the previously validated rows and writes them inside per-row savepoints, so one bad row can't roll back rows that already succeeded. Returns the final success/failure counts.
3. `GET /imports` — full history of every validate/commit attempt.

## Risk assessment flow

`POST /students/{id}/assess-risk` runs the engine for one student on demand (staff/admin only) and returns the new assessment. See `docs/RISK_ENGINE.md` for scoring details.
