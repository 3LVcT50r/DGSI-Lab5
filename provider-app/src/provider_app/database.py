from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from provider_app.config import settings
from provider_app.models import Base

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
