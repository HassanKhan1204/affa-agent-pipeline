"""
AFFA Outreach Agent — Step 3b: draft personalized outreach

What this does:
  Reads every lead in affa_crm.db that doesn't have an outreach_message yet,
  asks Claude to draft a short, personalized outreach email for each one
  (referencing the lead's specific fit reason), and writes the draft back
  into the database.

Run:
  python outreach_agent.py

Requires:
  affa_crm.db already built (run build_crm.py first)
  ANTHROPIC_API_KEY already set as an environment variable
"""

import sqlite3
from anthropic import Anthropic

client = Anthropic()

DB_PATH = "affa_crm.db"

AFFA_CONTEXT = """
A Farm For All is a 501(c)(3) community farm on 46 acres in Webatuck, New York
(Dutchess County, near the Connecticut border, roughly 90 minutes north of
New York City). It expands access to land, healthy food, agricultural
education, microgreens, herbs, youth programming, and community wellness for
under-served communities, families, and urban neighbors from the greater
NYC / Hudson Valley region.
"""

SYSTEM_PROMPT = """You write short, warm, specific outreach messages on behalf
of a small nonprofit community farm. You are NOT writing generic templates —
every message must reference the specific recipient's focus area and the
specific reason they're a good fit, in the recipient's own context.

Rules:
- 3-5 sentences maximum.
- No corporate jargon, no "I hope this email finds you well."
- Sound like a real person at a small nonprofit reaching out, not a mail
  merge.
- End with one clear, low-friction ask (e.g. a short call, a link to learn
  more about their program, an invitation to visit the farm).
- Do not invent facts about the recipient beyond what's given to you.
- Output ONLY the message text. No subject line, no preamble, no signature
  block beyond a simple sign-off with "A Farm For All" or a placeholder name.
"""


def draft_message(name: str, category: str, focus_area: str, fit_reason: str) -> str:
    relationship = "a potential funder" if category == "funder" else "a potential community partner"

    user_prompt = f"""
About A Farm For All:
{AFFA_CONTEXT}

Recipient: {name}
Relationship: {relationship}
Recipient's focus area: {focus_area}
Why this is a good fit: {fit_reason}

Draft the outreach message now.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return "".join(block.text for block in response.content if block.type == "text").strip()


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """SELECT id, name, category, focus_area, fit_reason
           FROM leads
           WHERE outreach_message IS NULL OR outreach_message = ''"""
    ).fetchall()

    print(f"Drafting outreach for {len(rows)} leads...\n")

    for row in rows:
        message = draft_message(
            row["name"], row["category"], row["focus_area"], row["fit_reason"]
        )
        conn.execute(
            "UPDATE leads SET outreach_message = ?, status = 'drafted' WHERE id = ?",
            (message, row["id"]),
        )
        conn.commit()

        print(f"--- {row['name']} ({row['category']}) ---")
        print(message)
        print()

    conn.close()
    print("Done. All outreach messages saved to affa_crm.db.")
