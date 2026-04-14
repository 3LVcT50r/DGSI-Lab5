from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from src.api.routes import api_router
from src.config import Settings
from src.database import engine, SessionLocal
import src.models as models
from src.services.seed import seed_database_from_config

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    models.Base.metadata.create_all(bind=engine)

    # Initialize database with seed data
    db = SessionLocal()
    try:
        seed_database_from_config(db, str(settings.default_config_path))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

    yield
    # Shutdown
    pass

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="REST API for the 3D Printer Factory Simulation System",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
