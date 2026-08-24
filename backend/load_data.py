"""
ETL: loads the agent pipeline's affa_crm.db (SQLite, the "batch" side —
written by build_crm.py + outreach_agent.py) into whatever DATABASE_URL
points at (Postgres in Docker, by default).

Upserts by `name`, so it's safe to re-run after every pipeline run: leads
already in the API keep their `status` (e.g. "contacted") and pick up any
new fields from the pipeline, while genuinely new leads get inserted.

Run:
  python load_data.py                       # uses ./affa_crm.db
  python load_data.py --source /path/to.db  # or point at a specific file
  docker compose run --rm backend python load_data.py
"""

import argparse
import sqlite3
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import Lead

SOURCE_COLUMNS = [
    "category",
    "name",
    "subtype",
    "focus_area",
    "fit_reason",
    "url",
    "contact_name",
    "contact_email",
    "contact_phone",
    "contact_page",
    "outreach_message",
    "status",
]


def read_source(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(
            f"{path} not found. Run the pipeline first "
            "(./run_pipeline.sh or `docker compose run --rm pipeline`)."
        )
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT {', '.join(SOURCE_COLUMNS)} FROM leads").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def upsert(rows: list[dict]) -> tuple[int, int]:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    inserted = updated = 0
    try:
        for row in rows:
            existing = db.query(Lead).filter(Lead.name == row["name"]).one_or_none()
            if existing is None:
                db.add(Lead(**row))
                inserted += 1
            else:
                # `status` is owned by the API from here on — a human might
                # have already moved this lead to "contacted" or beyond in
                # the UI, and every pipeline re-run resets the SQLite side's
                # status back to "drafted" (outreach_agent.py redrafts
                # everything after build_crm.py's rebuild). Re-syncing that
                # would silently undo real CRM progress, so every field
                # except status gets refreshed from the pipeline.
                row.pop("status")
                for field, value in row.items():
                    setattr(existing, field, value)
                updated += 1
        db.commit()
    finally:
        db.close()
    return inserted, updated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default="affa_crm.db",
        help="Path to the pipeline's SQLite database (default: ./affa_crm.db)",
    )
    args = parser.parse_args()

    rows = read_source(Path(args.source))
    print(f"Read {len(rows)} leads from {args.source}")

    inserted, updated = upsert(rows)
    print(f"Inserted {inserted}, updated {updated} ({inserted + updated} total) in the API database.")
