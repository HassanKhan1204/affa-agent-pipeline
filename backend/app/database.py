"""
SQLAlchemy engine/session setup, shared by the FastAPI app and load_data.py.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# SQLite needs this flag when used from multiple threads (FastAPI's default
# threadpool for sync endpoints); Postgres ignores it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a session, always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
