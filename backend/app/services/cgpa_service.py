from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ResultStatus
from app.models.result import CourseResult
from app.services.policy_service import get_policy


def compute_cgpa(db: Session, student_id: str) -> tuple[float | None, int, int]:
    """Returns (cgpa, completed_credits, total_attempted_credits).

    CGPA = sum(credits * grade_points) / sum(credits) over graded (pass/fail with
    grade points) results. Incomplete/withdrawn results are excluded from the
    calculation but counted in total_attempted_credits for transparency.
    """
    results = db.execute(select(CourseResult).where(CourseResult.student_id == student_id)).scalars().all()

    graded = [r for r in results if r.grade_points is not None and r.result_status in (ResultStatus.pass_, ResultStatus.fail)]
    total_weighted = sum(float(r.grade_points) * r.credits for r in graded)
    total_credits = sum(r.credits for r in graded)
    completed_credits = sum(r.credits for r in results if r.result_status == ResultStatus.pass_)
    total_attempted_credits = sum(r.credits for r in results)

    cgpa = round(total_weighted / total_credits, 2) if total_credits > 0 else None
    return cgpa, completed_credits, total_attempted_credits


def project_target_cgpa_scenarios(
    db: Session, student_id: str, remaining_credits: int, targets: list[float] | None = None
) -> list[dict]:
    """Estimate the average grade points needed across remaining credits to reach
    each target CGPA. This is a simplified, clearly-labelled projection, not an
    official policy calculation (see docs/ASSUMPTIONS.md)."""
    assumptions = get_policy(db, "cgpa_assumptions")
    max_gp = assumptions.get("max_grade_points", 10)

    cgpa, completed_credits, attempted_credits = compute_cgpa(db, student_id)
    graded_credits = attempted_credits
    current_weighted = (cgpa or 0) * graded_credits

    targets = targets or [7.0, 8.0, 9.0]
    scenarios = []
    for target in targets:
        if remaining_credits <= 0:
            scenarios.append(
                {
                    "target_cgpa": target,
                    "remaining_credits": 0,
                    "required_avg_grade_points": None,
                    "feasible": (cgpa or 0) >= target,
                    "note": "No remaining credits; target is only met if current CGPA already satisfies it.",
                }
            )
            continue
        total_credits_at_end = graded_credits + remaining_credits
        required_total_weighted = target * total_credits_at_end
        required_weighted_remaining = required_total_weighted - current_weighted
        required_avg_gp = required_weighted_remaining / remaining_credits
        feasible = 0 <= required_avg_gp <= max_gp
        scenarios.append(
            {
                "target_cgpa": target,
                "remaining_credits": remaining_credits,
                "required_avg_grade_points": round(required_avg_gp, 2),
                "feasible": feasible,
                "note": (
                    "Achievable with available grade scale." if feasible
                    else f"Requires an average grade point outside the assumed 0-{max_gp} scale; not realistically achievable."
                ),
            }
        )
    return scenarios
