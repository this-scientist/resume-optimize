from fastapi import FastAPI

from app.api.router import api

app = FastAPI(title="Resume Optimizer Local")
app.include_router(api)
