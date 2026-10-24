from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: str
    actor_user_id: str | None
    actor_name: str | None = None
    action: str
    entity_type: str
    entity_id: str | None
    before_data: dict | None
    after_data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
