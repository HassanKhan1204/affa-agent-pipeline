"""
Central settings for the backend. Everything comes from the environment so
the same image runs the same way in Docker, CI, or bare metal.

DATABASE_URL defaults to a local SQLite file so the API can be run without
Postgres at all (handy for a quick smoke test) — docker-compose always sets
it explicitly to point at the `db` service instead.
"""

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./affa_api.db")

# Comma-separated list of allowed origins for local, non-proxied dev (e.g.
# `npm run dev` on :5173 talking directly to the API on :8000). The
# dockerized UI never needs this — nginx proxies /api/ same-origin.
_default_origins = "http://localhost:5173,http://localhost:8080"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
