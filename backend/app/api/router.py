from fastapi import APIRouter

from app.api.routes import health, interview_sources, jobs, resumes, settings

api = APIRouter(prefix="/api")
api.include_router(health.router, tags=["health"])
api.include_router(interview_sources.router)
api.include_router(resumes.router)
api.include_router(jobs.router)
api.include_router(settings.router)
