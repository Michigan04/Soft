from pydantic import BaseModel

from app.models.enums import RegistrationStatus, ValidationStatus


class RegistrationValidateRequest(BaseModel):
    student_id: str
    academic_term_id: str
    course_ids: list[str]


class CourseValidationResult(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    is_valid: bool
    errors: list[str]


class RegistrationValidationResponse(BaseModel):
    student_id: str
    academic_term_id: str
    overall_valid: bool
    results: list[CourseValidationResult]


class RegistrationCreateRequest(BaseModel):
    student_id: str
    academic_term_id: str
    course_ids: list[str]


class RegistrationOut(BaseModel):
    id: str
    student_id: str
    course_id: str
    course_code: str
    course_name: str
    academic_term_id: str
    status: RegistrationStatus
    validation_status: ValidationStatus
    validation_errors: list[str] | None = None

    model_config = {"from_attributes": True}
