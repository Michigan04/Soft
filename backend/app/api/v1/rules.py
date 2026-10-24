from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_admin
from app.db.session import get_db
from app.models.policy import PolicySetting
from app.models.risk import RiskRule
from app.models.user import User
from app.schemas.risk import RiskRuleCreate, RiskRuleOut, RiskRuleUpdate
from app.services.audit_service import record_audit_event
from app.services.policy_service import DEFAULT_POLICIES, ensure_default_policies, get_policy, upsert_policy

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RiskRuleOut])
def list_rules(db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> list[RiskRule]:
    return db.execute(select(RiskRule).order_by(RiskRule.indicator_type)).scalars().all()


@router.post("", response_model=RiskRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RiskRuleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> RiskRule:
    if payload.threshold_value < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="threshold_value must be >= 0")
    rule = RiskRule(**payload.model_dump(), created_by=current_user.id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    record_audit_event(
        db, actor_user_id=current_user.id, action="create", entity_type="risk_rule", entity_id=rule.id,
        after_data=payload.model_dump(mode="json"),
    )
    return rule


@router.patch("/{rule_id}", response_model=RiskRuleOut)
def update_rule(
    rule_id: str, payload: RiskRuleUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> RiskRule:
    rule = db.get(RiskRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk rule not found")

    before = {
        "threshold_value": float(rule.threshold_value), "severity": rule.severity.value,
        "weight": float(rule.weight), "is_active": rule.is_active,
    }
    changes = payload.model_dump(exclude_unset=True)
    if "threshold_value" in changes and changes["threshold_value"] < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="threshold_value must be >= 0")
    for field, value in changes.items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)

    record_audit_event(
        db, actor_user_id=current_user.id, action="update", entity_type="risk_rule", entity_id=rule.id,
        before_data=before, after_data=changes,
    )
    return rule


@router.get("/policies")
def list_policies(db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> dict:
    ensure_default_policies(db)
    return {key: get_policy(db, key) for key in DEFAULT_POLICIES}


@router.put("/policies/{key}")
def update_policy(
    key: str, value: dict, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    if key not in DEFAULT_POLICIES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown policy key")
    before = get_policy(db, key)
    row = upsert_policy(db, key, value, current_user.id)
    record_audit_event(
        db, actor_user_id=current_user.id, action="update", entity_type="policy_setting", entity_id=key,
        before_data=before, after_data=value,
    )
    return row.value
