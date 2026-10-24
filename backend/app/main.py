from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.v1 import api_router
from app.core.config import settings
from app.db.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENABLE_DEMO_ACCOUNTS:
        try:
            if seed_if_empty():
                print("Database was empty - seeded demo accounts and sample data (see README for logins).")
        except (OperationalError, ProgrammingError) as e:
            print(f"Skipped demo auto-seed: could not read the users table ({e}). Run `alembic upgrade head` first.")
    yield


app = FastAPI(
    title="IITM BS Student Risk Identification and Intervention Platform",
    version="1.0.0",
    description=(
        "Rule-based risk identification, intervention tracking, and reporting platform "
        "for the IIT Madras BS Degree Program. See /docs for the full API reference."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/v1/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
