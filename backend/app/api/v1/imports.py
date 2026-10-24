from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_admin
from app.db.session import get_db
from app.models.data_import import DataImport
from app.models.enums import ImportStatus, ImportType
from app.models.user import User
from app.schemas.data_import import DataImportOut, ImportCommitRequest, ImportValidationResponse
from app.services.audit_service import record_audit_event
from app.services.import_service import commit_import, create_pending_import, mark_validated, parse_csv_text, validate_rows

router = APIRouter(prefix="/imports", tags=["imports"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.post("/validate", response_model=ImportValidationResponse)
async def validate_import(
    import_type: ImportType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ImportValidationResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv files are accepted")

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds the 5MB upload limit")

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be UTF-8 encoded text")

    rows = parse_csv_text(content)
    if not rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file has no data rows")

    valid_rows, row_errors = validate_rows(db, import_type, rows)

    data_import = create_pending_import(db, current_user.id, file.filename, import_type)
    data_import = mark_validated(db, data_import, valid_rows, row_errors, total_rows=len(rows))

    record_audit_event(
        db, actor_user_id=current_user.id, action="validate", entity_type="data_import", entity_id=data_import.id,
        after_data={"filename": file.filename, "total_rows": len(rows), "invalid_rows": len(row_errors)},
    )

    return ImportValidationResponse(
        import_type=import_type,
        total_rows=len(rows),
        valid_rows=len(valid_rows),
        invalid_rows=len(row_errors),
        row_errors=row_errors,
        preview=valid_rows[:10],
        validation_token=data_import.id,
    )


@router.post("/commit", response_model=DataImportOut)
def commit(payload: ImportCommitRequest, db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> DataImport:
    data_import = db.get(DataImport, payload.validation_token)
    if data_import is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation token not found")
    if data_import.status != ImportStatus.validated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This import has already been committed or was never validated")

    before = {"status": data_import.status.value}
    data_import = commit_import(db, data_import)

    record_audit_event(
        db, actor_user_id=current_user.id, action="commit", entity_type="data_import", entity_id=data_import.id,
        before_data=before,
        after_data={"status": data_import.status.value, "successful_rows": data_import.successful_rows, "failed_rows": data_import.failed_rows},
    )
    return data_import


@router.get("", response_model=list[DataImportOut])
def list_imports(db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> list[DataImport]:
    return db.execute(select(DataImport).order_by(DataImport.created_at.desc())).scalars().all()
