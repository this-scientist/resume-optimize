from fastapi import APIRouter

from app.api.routes import health

api = APIRouter(prefix="/api")
api.include_router(health.router, tags=["health"])
