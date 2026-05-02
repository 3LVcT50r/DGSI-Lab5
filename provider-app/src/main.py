"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import api_router
from src.config import Settings
from src.database import engine
from src.models import Base

settings = Settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup/shutdown lifecycle handler."""
    # Startup: create tables and seed DB
    Base.metadata.create_all(bind=engine)

    from src.services.seed import seed_database_from_config
    from src.database import SessionLocal

    with SessionLocal() as session:
        seed_database_from_config(
            session, settings.default_seed_path
        )

    yield
    # Shutdown: nothing needed


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "REST API for the 3D Printer "
        "Provider Simulation System"
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")