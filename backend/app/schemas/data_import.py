from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ImportStatus, ImportType


class RowError(BaseModel):
    row_number: int
    errors: list[str]


class ImportValidationResponse(BaseModel):
    import_type: ImportType
    total_rows: int
    valid_rows: int
    invalid_rows: int
    row_errors: list[RowError]
    preview: list[dict]
    validation_token: str


class ImportCommitRequest(BaseModel):
    validation_token: str


class DataImportOut(BaseModel):
    id: str
    filename: str
    import_type: ImportType
    status: ImportStatus
    total_rows: int
    successful_rows: int
    failed_rows: int
    created_at: datetime
    completed_at: datetime | None
    uploaded_by: str | None

    model_config = {"from_attributes": True}
