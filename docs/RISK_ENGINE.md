# Risk Identification Engine

`backend/app/services/risk_engine.py`

## What this is — and what it is not

This is a **transparent, rule-based scoring engine**, not a trained predictive model. It does not claim to predict dropout, and it is not validated against historical outcome data. Every number it produces can be traced back to a specific, admin-configured rule and an observed value in the student's own records. It uses only academic and engagement evidence already stored in the database — never demographic or other sensitive personal characteristics.

## Indicators

Each `risk_rules` row configures one of these indicator types (`RiskIndicatorType` in `app/models/enums.py`):

| Indicator | Observed value | Triggers when |
|---|---|---|
| `low_cgpa` | Current CGPA (credit-weighted) | observed `<` threshold |
| `failed_courses` | Count of `course_results` with status `fail` | observed `>=` threshold |
| `insufficient_credits` | Completed (passed) credits | observed `<` threshold |
| `missed_milestone` | Count of `student_milestones` with status `overdue` | observed `>=` threshold |
| `pending_courses` | Pending registrations + incomplete results | observed `>=` threshold |
| `incomplete_project` | Projects past `due_date` and not completed/submitted | observed `>=` threshold |
| `registration_failures` | Count of registration validation attempts where `overall_valid=false` | observed `>=` threshold |
| `inactivity` | Days since the student's most recent course result, registration, or intervention | observed `>=` threshold |
| `overdue_followup` | Open/in-progress interventions past their `follow_up_date` | observed `>=` threshold |

## Scoring formula

1. For every **active** rule whose `academic_level` is either unset or matches the student's level, evaluate whether it triggers (see table above).
2. A triggered rule contributes `severity_base_points(severity) * rule.weight`, where severity base points are fixed: `info=5`, `warning=15`, `critical=30`.
3. **Avoiding double-counting:** admins may configure several severity tiers for the same underlying indicator (e.g. a "Low CGPA" warning at threshold 5.0 and a "Critically low CGPA" critical rule at threshold 4.0). If more than one rule on the *same indicator type* triggers for a student, only the single highest-scoring rule for that indicator is kept — the others are suppressed so one underlying issue is never counted twice. This is enforced in code (`assess_student_risk`), not just by seed-data convention.
4. The final `risk_score = min(100, sum of kept rule points)` — a hard cap at 100.
5. The score maps to a category using admin-configurable cutoffs stored in `policy_settings["risk_level_thresholds"]` (defaults: `moderate >= 25`, `high >= 50`, `critical >= 75`; anything below is `low`).

## Explainability

Every triggered rule produces a `RiskFactor` row with: the observed value, the configured threshold, severity, a plain-language `explanation`, and a `recommended_action` (a fixed, per-indicator suggestion — e.g. "Schedule an academic counselling session..." for low CGPA). The `RiskAssessment.summary` states how many factors triggered and the resulting score/category. This is what the Student Profile → Risk Analysis tab renders directly.

## Handling missing data explicitly

If an indicator's underlying data doesn't exist yet (e.g. a brand-new student with zero course results has no computable CGPA), that indicator is **not silently treated as "no risk"**. It is recorded as *unavailable*, and the assessment's `data_completeness_note` lists exactly which indicators could not be evaluated, with wording that explicitly warns the assessment "should not be read as confirmation of low risk." Other indicators that *can* be evaluated from available data (e.g. `insufficient_credits`, since zero completed credits is itself a valid observed value) still run normally — a student isn't exempted from every rule just because one indicator is missing.

## History and change detection

- Every call to `assess_student_risk` **inserts a new** `risk_assessments` row; previous assessments are never updated or deleted, so a full history is always available (`GET /students/{id}/risk-assessments`).
- After a new assessment is saved, the engine compares its risk level against the immediately preceding assessment (ordinal order `low < moderate < high < critical`). If the level **increased**, or if this is the student's first assessment and it is already above `low`, the engine creates a `risk_escalation` notification for both the student and their assigned staff member (deduplicated per assessment so re-running the same assessment never double-notifies).

## Failure alerts (US-03)

Risk escalation notifications are triggered by the engine above. A separate, narrower alert — `notify_failed_result` (`services/notification_service.py`) — fires specifically when a new `fail` course result is recorded (currently invoked from the CSV import commit path for `course_results` imports). It is deduplicated per-result-row (`dedupe_key = failure_alert:{course_result.id}:...`) so re-importing or re-processing the same result never sends a duplicate alert. Email delivery uses a console/log "dev backend" when `SMTP_HOST` is unset, documented further in `docs/ASSUMPTIONS.md`.

## Configuring rules and thresholds

Admins manage everything above through `/api/v1/rules` (CRUD for `risk_rules`) and `/api/v1/rules/policies` (get/update `risk_level_thresholds` and `cgpa_assumptions`) — also exposed in the frontend's **Rules & Academic Policies** page. Every change is written to `audit_logs` with the before/after values and the acting admin.

## Known limitations

- The engine is intentionally simple and linear; it does not model interactions between indicators beyond the same-indicator-type dedup described above.
- `inactivity` only looks at course results, registrations, and interventions as "activity" — it has no visibility into, e.g., course-content engagement, since no such data exists in this schema.
- Risk-level thresholds and severity base-point values are global, not per-academic-level; only individual rules can be scoped to a level.
- This is evaluated synchronously on demand (`POST /students/{id}/assess-risk`) and automatically whenever certain import flows run; there is no scheduled/batch re-assessment job.
