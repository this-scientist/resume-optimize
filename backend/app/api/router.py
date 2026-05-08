from fastapi import APIRouter

from app.api.routes import health, interview_sources

api = APIRouter(prefix="/api")
api.include_router(health.router, tags=["health"])
api.include_router(interview_sources.router, tags=["interview-sources"])
