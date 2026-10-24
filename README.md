# IITM BS Student Risk Identification and Intervention Platform

A full-stack platform for identifying at-risk students in the IIT Madras BS Degree Program, explaining *why* they're at risk, notifying the right people, recommending next steps, and tracking interventions over time.

Stack: **FastAPI + SQLAlchemy 2.x + Alembic + PostgreSQL** backend, **Vue 3 + Vite + Pinia + Chart.js** frontend, JWT auth with role-based access control for `student` / `faculty` / `ta` / `admin`.

## Features (mapped to user stories)

| # | Feature | Where |
|---|---|---|
| US-01 | Progress dashboard (summary metrics, risk distribution, progression trends, alerts) | `/dashboard` |
| US-02 | Registration checker (prerequisite/level/duplicate validation) | `/registration-checker` |
| US-03 | Failure alerts + notification center (deduplicated, optional email) | `/notifications` |
| US-04 | Project & CGPA tracker with labelled target-CGPA projections | `/projects` |
| US-05 | At-risk / all-students list with filters, search, sort, pagination | `/students` |
| US-06 | Unified student profile (history, results, projects, risk, interventions, timeline) | `/students/:id` |
| US-07 | Intervention tracking with outcomes, history, overdue follow-ups | `/interventions`, student profile |
| US-08 | Staff assignment + workload | `/assignments` |
| US-09 | Configurable risk rules + policy thresholds | `/rules` |
| US-10 | CSV import with validate → commit, row-level error reporting | `/imports` |
| US-11 | Immutable audit log | `/audit-logs` |
| US-12 | Reports with CSV export | `/reports` |

See `docs/RISK_ENGINE.md` for exactly how risk scores are computed, `docs/DATABASE_DESIGN.md` for the schema, `docs/API_GUIDE.md` for the API, and **`docs/ASSUMPTIONS.md` for every simplification/limitation** — read that one before treating anything here as production-ready policy.

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 16 (via Docker, recommended) **or** your own PostgreSQL 14+ instance
- Docker + Docker Compose, if you want Postgres started for you

> ⚠️ This project was built in a sandbox with no working Docker/PostgreSQL available, so the schema was validated against SQLite instead (see `docs/ASSUMPTIONS.md`). **Before first real use, run the migration against an actual PostgreSQL database** and confirm it succeeds — it is expected to work (all types used are Postgres-compatible), but it has not been run against Postgres by the original build.

## 1. Clone and configure environment

```bash
cp .env.example .env
```

Edit `.env` if you want non-default DB credentials, a JWT secret, or real SMTP settings. Defaults work out of the box for local development.

## 2. Start PostgreSQL

**With Docker (recommended, all platforms):**

```bash
docker compose up -d
```

This starts Postgres on `localhost:5432` with the credentials from `.env`.

**Without Docker:** point `DATABASE_URL` in `.env` at your own running PostgreSQL instance and create the database named in `POSTGRES_DB` first.

## 3. Backend setup

### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run migrations

```bash
alembic upgrade head
```

### Seed demo data

```bash
python -m app.db.seed
```

This drops and recreates all tables, then inserts demo accounts, courses, milestones, risk rules, and 12 synthetic students spanning Foundation/Diploma/Degree with a realistic spread across Low/Moderate/High/Critical risk — including one student with **no** academic records at all, to demonstrate the "don't silently assume safe" missing-data handling. Re-run it any time to reset to a clean demo state.

### Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: **http://localhost:8000/docs**
- OpenAPI schema: **http://localhost:8000/openapi.json**
- Health check: `GET http://localhost:8000/api/v1/health`

## 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api/*` to `http://localhost:8000` (see `frontend/vite.config.js`), so both servers must be running.

For a production build: `npm run build` (output in `frontend/dist/`).

## 5. Demo accounts

All demo accounts share the password **`Demo@12345`**.

| Email | Role |
|---|---|
| `admin@demo.iitm.ac.in` | Administrator |
| `faculty1@demo.iitm.ac.in` | Faculty |
| `faculty2@demo.iitm.ac.in` | Faculty |
| `ta1@demo.iitm.ac.in` | Teaching Assistant |
| `23f1000003@demo.iitm.ac.in` | Student (high risk) |
| `22d2000002@demo.iitm.ac.in` | Student (critical risk) |
| `23f1000001@demo.iitm.ac.in` | Student (low risk) |

(Any of the 12 seeded student identifiers logs in as `<identifier>@demo.iitm.ac.in`.)

`ENABLE_DEMO_ACCOUNTS` in `.env.example` documents that these predictable credentials must never be enabled in a production deployment.

## 6. Running tests

```bash
cd backend
source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
pytest -q
```

The suite (43 tests) runs against an isolated in-memory SQLite database via dependency override — it does not touch your configured `DATABASE_URL` — and covers: login/RBAC, student data isolation, risk scoring + category thresholds + missing-data handling + history + escalation notifications, registration prerequisite validation, CGPA calculation and target-CGPA projection, intervention creation/history/overdue detection, CSV import validation (missing columns, invalid enums, duplicates, existing records) and commit, audit log creation and immutability, and report aggregation/filtering.

Frontend: `cd frontend && npm test` — 18 Vitest unit tests covering the risk badge color/labeling logic, the API error-message helper, the auth store's role getters, and the pagination component's button states and events.

## 7. Email / SMTP

SMTP is optional. Leave `SMTP_HOST` empty in `.env` to use the built-in console/log email backend (every "sent" email is written to the backend log instead), so the whole app is demoable without a mail server. Set `SMTP_HOST`/`SMTP_PORT`/`SMTP_USERNAME`/`SMTP_PASSWORD` to send real email.

## 8. Deploying to Vercel

The repo deploys as a single Vercel project: the Vue app is built to static files, and the FastAPI backend runs as one Python serverless function (`api/index.py`) on the same domain, so no CORS setup is needed. `vercel.json` wires it up:

- `/api/*`, `/docs`, `/redoc`, `/openapi.json` → FastAPI function
- `/html/` → the no-build `frontend-html/` port (it calls the same-origin API when not on localhost)
- everything else → the Vue SPA (`frontend/dist`)

**1. Create a hosted PostgreSQL database.** Vercel can't reach a local Postgres. Any hosted Postgres works, e.g. Neon (Vercel Marketplace → Neon), Supabase or Railway. Use the **pooled** connection string if the provider offers one. `postgres://` / `postgresql://` URLs are accepted as-is (they're rewritten to the `psycopg` driver automatically).

**2. Create the schema and (optionally) demo data** from your machine, pointed at that database:

```bash
cd backend
DATABASE_URL="postgresql://...your hosted db..." alembic upgrade head
# optional demo accounts + sample data (only on an empty DB):
DATABASE_URL="postgresql://..." python -c "from app.db.seed import seed_if_empty; seed_if_empty()"
```

(PowerShell: `$env:DATABASE_URL="postgresql://..."` on its own line first.)

**3. Import the repo in Vercel** (or run `vercel` from the repo root). Leave the Root Directory as the repo root and the framework preset as "Other"; build settings come from `vercel.json`. Set these environment variables:

| Variable | Value |
|---|---|
| `DATABASE_URL` | the hosted Postgres URL |
| `JWT_SECRET_KEY` | a long random string (e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`) |
| `ENVIRONMENT` | `production` |
| `ENABLE_DEMO_ACCOUNTS` | `false` (or `true` only for a demo deployment) |
| `SMTP_*` | optional, same as local |

`CORS_ORIGINS` isn't needed, since the frontend and API share an origin.

**Serverless caveats:** each request opens a fresh DB connection (the app uses `NullPool` when `VERCEL` is set), so prefer a pooled connection string. Function requests time out after 30s (`maxDuration` in `vercel.json`) and request bodies are capped at 4.5 MB, which limits CSV import size. Email sending only works with real SMTP settings.

## Project layout

```
backend/app/
  core/        config, security (JWT/password hashing), permissions (RBAC dependencies)
  db/          session, declarative base + portable GUID type, seed script
  models/      SQLAlchemy models (one file per domain area)
  schemas/     Pydantic request/response schemas
  api/v1/      FastAPI routers, one per resource area
  services/    business logic: risk_engine, registration, cgpa, notifications,
               interventions, imports, reporting, audit, policy
  tests/       pytest suite
alembic/       migrations
frontend/src/
  api/         one module per backend resource area (axios)
  stores/      Pinia stores (auth, notifications)
  router/      Vue Router with role-based navigation guards
  layouts/     AppLayout (sidebar + header shell)
  components/  reusable UI (badges, cards, tables helpers, charts, forms, dialogs)
  views/       one component per page/user story
docs/          DATABASE_DESIGN.md, RISK_ENGINE.md, API_GUIDE.md, ASSUMPTIONS.md
```

## Known limitations

See `docs/ASSUMPTIONS.md` for the full list. Headline items: the schema has been validated against SQLite, not yet against a live PostgreSQL instance (verify before production use); frontend tests are unit-level only (no page-level integration tests); CGPA/risk-rule numeric defaults are our own configurable assumptions, not official IITM policy.
