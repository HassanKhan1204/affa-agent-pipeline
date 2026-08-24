"""
AFFA CRM — Step 3a: build the database

What this does:
  Reads funders.json and partners.json (produced by the earlier agents) and
  loads them into a single SQLite database with one unified `leads` table.
  This is the "populated CRM" piece of the demo.

Run:
  python build_crm.py

Requires:
  Nothing extra — sqlite3 is built into Python. Just make sure funders.json
  and partners.json already exist in this folder (run funding_agent.py and
  partnership_agent.py first if you haven't).
"""

import json
import sqlite3

DB_PATH = "affa_crm.db"


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,       -- 'funder' or 'partner'
            name TEXT NOT NULL,
            subtype TEXT,                 -- e.g. 'grant', 'school', 'healthcare'
            focus_area TEXT,
            fit_reason TEXT,              -- unified: fit_reason or partnership_angle
            url TEXT,
            contact_name TEXT,            -- named contact person, if known
            contact_email TEXT,           -- best available email
            contact_phone TEXT,           -- best available phone number
            contact_page TEXT,            -- specific contact/inquiries page
            outreach_message TEXT,        -- filled in later by outreach_agent.py
            status TEXT DEFAULT 'new'     -- new -> contacted -> responded -> etc
        )
    """)
    conn.commit()


def load_json(path: str) -> list[dict]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {path} not found, skipping.")
        return []


def insert_funders(conn: sqlite3.Connection, funders: list[dict]) -> int:
    rows = [
        (
            "funder",
            f.get("name", ""),
            f.get("type", ""),
            f.get("focus_area", ""),
            f.get("fit_reason", ""),
            f.get("url", ""),
            f.get("contact_name", ""),
            f.get("contact_email", ""),
            f.get("contact_phone", ""),
            f.get("contact_page", ""),
        )
        for f in funders
    ]
    conn.executemany(
        """INSERT INTO leads (category, name, subtype, focus_area, fit_reason, url,
                               contact_name, contact_email, contact_phone, contact_page)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    return len(rows)


def insert_partners(conn: sqlite3.Connection, partners: list[dict]) -> int:
    rows = [
        (
            "partner",
            p.get("name", ""),
            p.get("type", ""),
            p.get("focus_area", ""),
            p.get("partnership_angle", ""),
            p.get("url", ""),
            p.get("contact_name", ""),
            p.get("contact_email", ""),
            p.get("contact_phone", ""),
            p.get("contact_page", ""),
        )
        for p in partners
    ]
    conn.executemany(
        """INSERT INTO leads (category, name, subtype, focus_area, fit_reason, url,
                               contact_name, contact_email, contact_phone, contact_page)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    return len(rows)


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Clear existing rows so re-running this script doesn't duplicate leads
    conn.execute("DELETE FROM leads")
    conn.commit()

    funders = load_json("funders.json")
    partners = load_json("partners.json")

    n_funders = insert_funders(conn, funders)
    n_partners = insert_partners(conn, partners)

    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

    print(f"Loaded {n_funders} funders and {n_partners} partners.")
    print(f"Total leads in {DB_PATH}: {total}")

    conn.close()
