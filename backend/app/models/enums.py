import enum


class UserRole(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    ta = "ta"
    admin = "admin"


class AcademicLevel(str, enum.Enum):
    foundation = "foundation"
    diploma = "diploma"
    degree = "degree"


class ProgramStatus(str, enum.Enum):
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    discontinued = "discontinued"


class RegistrationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class ValidationStatus(str, enum.Enum):
    valid = "valid"
    invalid = "invalid"
    not_validated = "not_validated"


class ResultStatus(str, enum.Enum):
    pass_ = "pass"
    fail = "fail"
    incomplete = "incomplete"
    withdrawn = "withdrawn"


class MilestoneStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    overdue = "overdue"


class ProjectStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    submitted = "submitted"
    completed = "completed"
    overdue = "overdue"


class RiskLevel(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class Severity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class NotificationType(str, enum.Enum):
    failure_alert = "failure_alert"
    risk_escalation = "risk_escalation"
    intervention_followup = "intervention_followup"
    registration_result = "registration_result"
    general = "general"


class DeliveryChannel(str, enum.Enum):
    in_app = "in_app"
    email = "email"


class DeliveryStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    skipped = "skipped"


class InterventionType(str, enum.Enum):
    call = "call"
    email = "email"
    meeting = "meeting"
    academic_counselling = "academic_counselling"
    remedial_recommendation = "remedial_recommendation"
    other = "other"


class InterventionStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class InterventionOutcome(str, enum.Enum):
    improved = "improved"
    no_change = "no_change"
    further_support_required = "further_support_required"
    unable_to_contact = "unable_to_contact"


class ImportType(str, enum.Enum):
    students = "students"
    course_results = "course_results"
    registrations = "registrations"
    projects = "projects"


class ImportStatus(str, enum.Enum):
    pending = "pending"
    validated = "validated"
    committed = "committed"
    failed = "failed"


class RiskIndicatorType(str, enum.Enum):
    low_cgpa = "low_cgpa"
    failed_courses = "failed_courses"
    insufficient_credits = "insufficient_credits"
    missed_milestone = "missed_milestone"
    pending_courses = "pending_courses"
    incomplete_project = "incomplete_project"
    registration_failures = "registration_failures"
    inactivity = "inactivity"
    overdue_followup = "overdue_followup"
