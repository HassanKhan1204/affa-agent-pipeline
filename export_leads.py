"""
AFFA CRM Export — feeds the React table UI

What this does:
  Reads affa_crm.db and writes leads.json — a flat JSON array the React
  app loads directly. Re-run this any time your CRM data changes and you
  want the UI to reflect it.

Run:
  python export_leads.py
"""

import json
import sqlite3

conn = sqlite3.connect("affa_crm.db")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    """SELECT id, category, name, subtype, focus_area, fit_reason, url,
              outreach_message, status
       FROM leads ORDER BY category, name"""
).fetchall()

leads = [dict(row) for row in rows]

with open("leads.json", "w", encoding="utf-8") as f:
    json.dump(leads, f, indent=2)

print(f"Exported {len(leads)} leads to leads.json")
conn.close()
