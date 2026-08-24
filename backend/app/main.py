from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.routers import leads

# Dev convenience only: creates tables if they don't exist yet (e.g. a
# fresh Postgres volume, or the default local sqlite fallback). In
# production this would be a real migration (Alembic); for a project this
# size, create_all on startup is the pragmatic choice — see load_data.py,
# which is the actual source of truth for schema + data via the pipeline.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AFFA CRM API",
    description="Serves funder/partner leads researched by the AFFA agent pipeline.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "PATCH"],
    allow_headers=["*"],
)

app.include_router(leads.router)
