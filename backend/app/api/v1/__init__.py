from fastapi import APIRouter

from app.api.v1 import (
    academic,
    assignments,
    audit,
    auth,
    dashboard,
    imports,
    interventions,
    notifications,
    projects,
    registrations,
    reports,
    rules,
    students,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(academic.router)
api_router.include_router(dashboard.router)
api_router.include_router(students.router)
api_router.include_router(registrations.router)
api_router.include_router(projects.router)
api_router.include_router(projects.router_milestones)
api_router.include_router(interventions.router)
api_router.include_router(assignments.router)
api_router.include_router(notifications.router)
api_router.include_router(rules.router)
api_router.include_router(imports.router)
api_router.include_router(audit.router)
api_router.include_router(reports.router)
