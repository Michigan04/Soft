"""Synthetic development seed data.

Run with: python -m app.db.seed
Creates demo accounts (documented in README), courses, terms, milestones,
risk rules, and a realistic mix of students across Foundation/Diploma/Degree
with varied risk profiles, so the whole application is demoable immediately.
All data is synthetic; no real student records are used.
"""

import random
from datetime import date, timedelta

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.academic import AcademicTerm, Course, CoursePrerequisite
from app.models.audit import AuditLog
from app.models.enums import (
    AcademicLevel,
    DeliveryChannel,
    DeliveryStatus,
    ImportStatus,
    ImportType,
    InterventionOutcome,
    InterventionStatus,
    InterventionType,
    MilestoneStatus,
    NotificationType,
    ProgramStatus,
    ProjectStatus,
    RegistrationStatus,
    ResultStatus,
    RiskIndicatorType,
    Severity,
    UserRole,
    ValidationStatus,
)
from app.models.intervention import Intervention, InterventionHistory
from app.models.milestone import AcademicMilestone, StudentMilestone
from app.models.notification import Notification, NotificationDelivery
from app.models.project import Project
from app.models.registration import Registration, RegistrationValidationLog
from app.models.result import CourseResult
from app.models.risk import RiskRule
from app.models.student import Student
from app.models.user import User
from app.services.policy_service import ensure_default_policies
from app.services.risk_engine import assess_student_risk

random.seed(42)

DEMO_PASSWORD = "Demo@12345"


def reset_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_if_empty() -> bool:
    """Seed demo data only when the users table has nothing in it yet.

    Used on app startup (see app/main.py) so a fresh database always has demo
    accounts to log in with, without ever touching/wiping a database that
    already has real data in it. Returns True if it actually seeded.
    """
    db = SessionLocal()
    try:
        if db.query(User).first() is not None:
            return False
    finally:
        db.close()
    seed()
    return True


def seed():
    db = SessionLocal()
    try:
        ensure_default_policies(db)

        # --- Demo accounts (one per role) ---
        admin = User(email="admin@demo.iitm.ac.in", password_hash=hash_password(DEMO_PASSWORD), full_name="Admin Admin", role=UserRole.admin)
        faculty1 = User(email="faculty1@demo.iitm.ac.in", password_hash=hash_password(DEMO_PASSWORD), full_name="Dr. Rekha Nair", role=UserRole.faculty)
        faculty2 = User(email="faculty2@demo.iitm.ac.in", password_hash=hash_password(DEMO_PASSWORD), full_name="Dr. Suresh Pillai", role=UserRole.faculty)
        ta1 = User(email="ta1@demo.iitm.ac.in", password_hash=hash_password(DEMO_PASSWORD), full_name="Ananya Kulkarni", role=UserRole.ta)
        db.add_all([admin, faculty1, faculty2, ta1])
        db.flush()

        # --- Academic terms ---
        term_prev = AcademicTerm(name="Jan 2026 Term", start_date=date(2026, 1, 5), end_date=date(2026, 5, 10), is_active=False)
        term_curr = AcademicTerm(name="Sep 2026 Term", start_date=date(2026, 9, 1), end_date=date(2027, 1, 15), is_active=True)
        db.add_all([term_prev, term_curr])
        db.flush()

        # --- Courses ---
        course_defs = [
            ("MATH1001", "Mathematics for Data Science I", 4, AcademicLevel.foundation),
            ("STAT1002", "Statistics for Data Science I", 4, AcademicLevel.foundation),
            ("CT1001", "Computational Thinking", 4, AcademicLevel.foundation),
            ("ENG1001", "English I", 4, AcademicLevel.foundation),
            ("MATH1003", "Mathematics for Data Science II", 4, AcademicLevel.foundation),
            ("PY1001", "Programming in Python", 4, AcademicLevel.diploma),
            ("DB1001", "Database Management Systems", 4, AcademicLevel.diploma),
            ("PDSA1001", "Programming, Data Structures and Algorithms", 4, AcademicLevel.diploma),
            ("MLF1001", "Machine Learning Foundations", 4, AcademicLevel.diploma),
            ("MLT1001", "Machine Learning Techniques", 4, AcademicLevel.diploma),
            ("SE1001", "Software Engineering", 4, AcademicLevel.degree),
            ("DL1001", "Deep Learning", 4, AcademicLevel.degree),
            ("AI1001", "AI: Search Methods for Problem Solving", 4, AcademicLevel.degree),
            ("ST1001", "Software Testing", 4, AcademicLevel.degree),
            ("BA1001", "Business Analytics", 4, AcademicLevel.degree),
        ]
        courses = {}
        for code, name, credits, level in course_defs:
            c = Course(course_code=code, course_name=name, credits=credits, academic_level=level, is_active=True)
            db.add(c)
            courses[code] = c
        db.flush()

        db.add_all([
            CoursePrerequisite(course_id=courses["MATH1003"].id, prerequisite_course_id=courses["MATH1001"].id, minimum_grade_points=4.0),
            CoursePrerequisite(course_id=courses["PDSA1001"].id, prerequisite_course_id=courses["PY1001"].id, minimum_grade_points=4.0),
            CoursePrerequisite(course_id=courses["MLT1001"].id, prerequisite_course_id=courses["MLF1001"].id, minimum_grade_points=5.0),
            CoursePrerequisite(course_id=courses["DL1001"].id, prerequisite_course_id=courses["MLT1001"].id, minimum_grade_points=5.0),
            CoursePrerequisite(course_id=courses["SE1001"].id, prerequisite_course_id=courses["PDSA1001"].id, minimum_grade_points=4.0),
        ])

        # --- Academic milestones ---
        milestones = {
            AcademicLevel.foundation: AcademicMilestone(
                name="Foundation Level Completion", academic_level=AcademicLevel.foundation,
                description="Complete all 8 foundation-level courses.", required_credits=32, target_cgpa=4.0, sequence_order=1,
            ),
            AcademicLevel.diploma: AcademicMilestone(
                name="Diploma Level Completion", academic_level=AcademicLevel.diploma,
                description="Complete diploma-level courses and qualifying project.", required_credits=27, target_cgpa=4.0, sequence_order=1,
            ),
            AcademicLevel.degree: AcademicMilestone(
                name="Degree Level Completion", academic_level=AcademicLevel.degree,
                description="Complete degree-level courses and final project.", required_credits=32, target_cgpa=4.0, sequence_order=1,
            ),
        }
        db.add_all(milestones.values())
        db.flush()

        # --- Risk rules (configurable, seeded as sensible defaults) ---
        rules = [
            RiskRule(name="Low CGPA", indicator_type=RiskIndicatorType.low_cgpa, threshold_value=5.0, severity=Severity.warning, weight=1.5, created_by=admin.id),
            RiskRule(name="Critically low CGPA", indicator_type=RiskIndicatorType.low_cgpa, threshold_value=4.0, severity=Severity.critical, weight=1.0, created_by=admin.id),
            RiskRule(name="Failed courses", indicator_type=RiskIndicatorType.failed_courses, threshold_value=1, severity=Severity.warning, weight=1.0, created_by=admin.id),
            RiskRule(name="Repeated failures", indicator_type=RiskIndicatorType.failed_courses, threshold_value=2, severity=Severity.critical, weight=1.0, created_by=admin.id),
            RiskRule(name="Insufficient completed credits", indicator_type=RiskIndicatorType.insufficient_credits, threshold_value=4, severity=Severity.warning, weight=1.0, created_by=admin.id),
            RiskRule(name="Missed milestones", indicator_type=RiskIndicatorType.missed_milestone, threshold_value=1, severity=Severity.warning, weight=1.0, created_by=admin.id),
            RiskRule(name="High pending/incomplete course load", indicator_type=RiskIndicatorType.pending_courses, threshold_value=2, severity=Severity.info, weight=1.0, created_by=admin.id),
            RiskRule(name="Overdue project", indicator_type=RiskIndicatorType.incomplete_project, threshold_value=1, severity=Severity.warning, weight=1.2, created_by=admin.id),
            RiskRule(name="Repeated registration failures", indicator_type=RiskIndicatorType.registration_failures, threshold_value=2, severity=Severity.info, weight=1.0, created_by=admin.id),
            RiskRule(name="Prolonged inactivity", indicator_type=RiskIndicatorType.inactivity, threshold_value=45, severity=Severity.warning, weight=1.0, created_by=admin.id),
            RiskRule(name="Overdue intervention follow-up", indicator_type=RiskIndicatorType.overdue_followup, threshold_value=1, severity=Severity.info, weight=0.8, created_by=admin.id),
        ]
        db.add_all(rules)
        db.flush()

        # --- Students ---
        student_profiles = [
            # (identifier, name, level, risk profile)
            ("23f1000001", "Aditi Sharma", AcademicLevel.foundation, "low"),
            ("23f1000002", "Rohan Verma", AcademicLevel.foundation, "moderate"),
            ("23f1000003", "Priya Reddy", AcademicLevel.foundation, "high"),
            ("23f1000004", "Karan Mehta", AcademicLevel.foundation, "low"),
            ("22d2000001", "Sneha Iyer", AcademicLevel.diploma, "low"),
            ("22d2000002", "Vikram Singh", AcademicLevel.diploma, "critical"),
            ("22d2000003", "Neha Joshi", AcademicLevel.diploma, "moderate"),
            ("22d2000004", "Arjun Rao", AcademicLevel.diploma, "unassessed"),
            ("21g3000001", "Divya Krishnan", AcademicLevel.degree, "low"),
            ("21g3000002", "Manish Gupta", AcademicLevel.degree, "high"),
            ("21g3000003", "Pooja Desai", AcademicLevel.degree, "critical"),
            ("21g3000004", "Siddharth Rao", AcademicLevel.degree, "moderate"),
        ]

        level_courses = {
            AcademicLevel.foundation: ["MATH1001", "STAT1002", "CT1001", "ENG1001", "MATH1003"],
            AcademicLevel.diploma: ["PY1001", "DB1001", "PDSA1001", "MLF1001", "MLT1001"],
            AcademicLevel.degree: ["SE1001", "DL1001", "AI1001", "ST1001", "BA1001"],
        }
        staff_cycle = [faculty1.id, faculty2.id, ta1.id, None]

        students = []
        for idx, (ident, name, level, profile) in enumerate(student_profiles):
            email = f"{ident}@demo.iitm.ac.in"
            user = User(email=email, password_hash=hash_password(DEMO_PASSWORD), full_name=name, role=UserRole.student)
            db.add(user)
            db.flush()

            assigned_staff = staff_cycle[idx % len(staff_cycle)]
            student = Student(
                student_identifier=ident, user_id=user.id, full_name=name, academic_level=level,
                program_status=ProgramStatus.active, admission_date=date(2023, 1, 10) - timedelta(days=365 * (idx % 3)),
                current_term=term_curr.name, assigned_staff_id=assigned_staff,
            )
            db.add(student)
            db.flush()
            students.append((student, profile))

            # Milestone progress: mark the level milestone in_progress by default
            sm = StudentMilestone(student_id=student.id, milestone_id=milestones[level].id, status=MilestoneStatus.in_progress)
            if profile in ("high", "critical"):
                sm.status = MilestoneStatus.overdue
                sm.notes = "Behind required pace for this milestone."
            db.add(sm)

            codes = level_courses[level]
            # Grade plans are deliberately tuned so each profile lands in its
            # intended risk bucket under the scoring formula in docs/RISK_ENGINE.md:
            #   low ~0 pts, moderate ~25-49, high ~50-74, critical ~75-100.
            grade_plan = {
                "low": [8, 7, 9, 8, 7],
                "moderate": [4, 4, 5, 5, 4],
                "high": [3, 5, 5, 5, 5],
                "critical": [2, 2, 5, 5, 5],
                "unassessed": [],
            }[profile]

            if profile != "unassessed":
                for code, gp in zip(codes, grade_plan):
                    course = courses[code]
                    result_status = ResultStatus.fail if gp <= 3 else ResultStatus.pass_
                    db.add(CourseResult(
                        student_id=student.id, course_id=course.id, academic_term_id=term_prev.id,
                        grade="F" if result_status == ResultStatus.fail else "B",
                        grade_points=gp, credits=course.credits, result_status=result_status,
                        recorded_at=term_prev.end_date,
                    ))

                # Current-term registrations: everyone has at least one (recent
                # activity), moderate/high/critical have two (crosses the
                # "high pending course load" threshold of 2).
                pending_count = 1 if profile == "low" else 2
                for code in codes[:pending_count]:
                    db.add(Registration(
                        student_id=student.id, course_id=courses[code].id, academic_term_id=term_curr.id,
                        status=RegistrationStatus.pending, validation_status=ValidationStatus.not_validated,
                    ))

            # Projects: vary status (foundation level has no project yet)
            if level != AcademicLevel.foundation and profile != "unassessed":
                proj_status_map = {
                    "low": ProjectStatus.completed, "moderate": ProjectStatus.in_progress,
                    "high": ProjectStatus.in_progress, "critical": ProjectStatus.overdue,
                }
                status = proj_status_map[profile]
                due = date.today() - timedelta(days=10) if status == ProjectStatus.overdue else date.today() + timedelta(days=30)
                db.add(Project(
                    student_id=student.id, title=f"{level.value.title()} Capstone Project", status=status,
                    start_date=date.today() - timedelta(days=60), due_date=due,
                    completion_date=date.today() - timedelta(days=5) if status == ProjectStatus.completed else None,
                    grade="A" if status == ProjectStatus.completed else None,
                    supervisor_id=assigned_staff if assigned_staff in (faculty1.id, faculty2.id) else faculty1.id,
                ))

            # Repeated registration validation failures only for the critical archetype
            if profile == "critical":
                db.add(RegistrationValidationLog(
                    student_id=student.id, academic_term_id=term_curr.id,
                    requested_courses=[courses[codes[2]].id],
                    validation_result={"overall_valid": False, "results": [{"course_id": courses[codes[2]].id, "is_valid": False, "errors": ["Missing prerequisite."]}]},
                ))
                db.add(RegistrationValidationLog(
                    student_id=student.id, academic_term_id=term_curr.id,
                    requested_courses=[courses[codes[3]].id],
                    validation_result={"overall_valid": False, "results": [{"course_id": courses[codes[3]].id, "is_valid": False, "errors": ["Already registered."]}]},
                ))

        db.commit()

        # --- Interventions (varied statuses/outcomes/follow-ups) ---
        for student, profile in students:
            if profile == "low" or profile == "unassessed":
                continue
            staff_id = student.assigned_staff_id or faculty1.id
            interv = Intervention(
                student_id=student.id, staff_user_id=staff_id, intervention_type=InterventionType.call,
                description="Initial check-in call regarding recent academic performance.",
                status=InterventionStatus.completed, outcome=InterventionOutcome.no_change,
                follow_up_date=date.today() - timedelta(days=20),
                completed_at=None,
            )
            db.add(interv)
            db.flush()
            db.add(InterventionHistory(intervention_id=interv.id, changed_by=staff_id, field_changed="created", old_value=None, new_value="call"))

            if profile in ("high", "critical"):
                interv2 = Intervention(
                    student_id=student.id, staff_user_id=staff_id, intervention_type=InterventionType.academic_counselling,
                    description="Scheduled academic counselling session to discuss remedial plan.",
                    status=InterventionStatus.open, follow_up_date=date.today() - timedelta(days=2),
                )
                db.add(interv2)
                db.flush()
                db.add(InterventionHistory(intervention_id=interv2.id, changed_by=staff_id, field_changed="created", old_value=None, new_value="academic_counselling"))

        db.commit()

        # --- Run risk engine for every student (creates history + notifications) ---
        for student, _profile in students:
            assess_student_risk(db, student)
        # Run a second pass for a couple of students to simulate a risk-level change over time
        for student, profile in students:
            if profile in ("high", "critical"):
                assess_student_risk(db, student)

        # --- A few read/unread general notifications for variety ---
        for student, profile in students[:3]:
            db.add(Notification(
                user_id=student.user_id, student_id=student.id, notification_type=NotificationType.general,
                title="Welcome to the Sep 2026 Term", message="Registration is open; please review your course plan.",
                severity=Severity.info, is_read=(profile == "low"),
            ))
        db.commit()

        # --- A sample completed data import for history/demo ---
        sample_import = None
        from app.models.data_import import DataImport
        sample_import = DataImport(
            uploaded_by=admin.id, filename="sample_course_results_2026_01.csv", import_type=ImportType.course_results,
            status=ImportStatus.committed, total_rows=5, successful_rows=5, failed_rows=0,
        )
        db.add(sample_import)

        # --- Audit trail samples ---
        db.add(AuditLog(actor_user_id=admin.id, action="seed", entity_type="system", entity_id=None, after_data={"note": "Initial demo data seeded."}))
        db.commit()

        print(f"Seed complete: {len(students)} students, {len(rules)} risk rules, {len(courses)} courses.")
        print(f"Demo password for all accounts: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    reset_schema()
    seed()
