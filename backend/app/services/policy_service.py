from sqlalchemy.orm import Session

from app.models.policy import PolicySetting

DEFAULT_POLICIES: dict[str, dict] = {
    "risk_level_thresholds": {
        "moderate": 25,
        "high": 50,
        "critical": 75,
        "_note": "A risk_score (0-100) >= a threshold places the student at that level or above.",
    },
    "cgpa_assumptions": {
        "max_grade_points": 10,
        "default_course_credits": 4,
        "_note": (
            "Grade-point scale and default credits used for CGPA / target-CGPA projections. "
            "These are DEVELOPMENT ASSUMPTIONS, not official IITM policy."
        ),
    },
    "inactivity_window_days": {
        "days": 45,
        "_note": "Minimum days of registered inactivity before the inactivity indicator can trigger.",
    },
}


def get_policy(db: Session, key: str) -> dict:
    row = db.query(PolicySetting).filter(PolicySetting.key == key).one_or_none()
    if row is not None:
        return row.value
    return DEFAULT_POLICIES.get(key, {})


def ensure_default_policies(db: Session) -> None:
    for key, value in DEFAULT_POLICIES.items():
        existing = db.query(PolicySetting).filter(PolicySetting.key == key).one_or_none()
        if existing is None:
            db.add(PolicySetting(key=key, value=value, description=value.get("_note")))
    db.commit()


def upsert_policy(db: Session, key: str, value: dict, updated_by: str | None) -> PolicySetting:
    row = db.query(PolicySetting).filter(PolicySetting.key == key).one_or_none()
    if row is None:
        row = PolicySetting(key=key, value=value, updated_by=updated_by)
        db.add(row)
    else:
        row.value = value
        row.updated_by = updated_by
    db.commit()
    db.refresh(row)
    return row
