from fastapi import APIRouter

from app.api.v1.routes import admin, employees, integrations, reports, sprints, system, teams

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(teams.router)
api_router.include_router(employees.router)
api_router.include_router(sprints.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
api_router.include_router(integrations.router)
