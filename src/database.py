from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import Settings

settings = Settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
