from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import api_router
from src.config import Settings
from src.database import engine
import src.models as models

settings = Settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="REST API for the 3D Printer Factory Simulation System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}
