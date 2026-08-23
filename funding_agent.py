"""
AFFA Funding Agent — with daily dedup support

What this does:
  Loads any existing funders.json, tells Claude which funders it already
  has, and asks it to find NEW ones not already in the list. Merges and
  saves back to funders.json. Safe to run daily via GitHub Actions — each
  run grows the list instead of replacing it.

Run:
  python funding_agent.py

Requires:
  pip install anthropic
  ANTHROPIC_API_KEY set as an environment variable
"""

import json
import os
from anthropic import Anthropic

client = Anthropic()

AFFA_MISSION = """
A Farm For All is a 501(c)(3) community farm on 46 acres in Webatuck, New York
(Dutchess County, near the Connecticut border, roughly 90 minutes north of
New York City). It works to expand access to land, healthy food, agricultural
education, microgreens, herbs, youth programming, and community wellness for
under-served communities, families, and urban neighbors from the greater
NYC / Hudson Valley region.
"""

SYSTEM_PROMPT = """You are a research agent for a nonprofit. You use web search
to find REAL, currently active funding opportunities (grants, foundations,
corporate sponsorship programs, government programs) that plausibly fit the
nonprofit's mission.

After researching, respond with ONLY a JSON array (no markdown fences, no
preamble, no commentary) where each item has this exact shape:

{
  "name": "string - name of the funder/program",
  "type": "grant | foundation | corporate | government",
  "focus_area": "string - what they fund",
  "fit_reason": "string - 1 sentence on why this fits A Farm For All specifically",
  "url": "string - link if found, else empty string"
}

Only include real organizations/programs you found through search. If you
are not confident something is real and current, leave it out rather than
guessing. Do NOT include any organization already in the "already found"
list you're given — every result must be new.
"""

FUNDERS_PATH = "funders.json"


def load_existing() -> list[dict]:
    if os.path.exists(FUNDERS_PATH):
        with open(FUNDERS_PATH, "r") as f:
            return json.load(f)
    return []


def find_new_funders(mission: str, existing: list[dict], count: int = 5) -> list[dict]:
    existing_names = [f["name"] for f in existing]
    existing_list_text = "\n".join(f"- {name}" for name in existing_names) or "(none yet)"

    user_prompt = f"""
Nonprofit mission:
{mission}

We already have these funders in our list — do NOT repeat any of them:
{existing_list_text}

Research and return {count} NEW real funding opportunities (grants,
foundations, corporate sponsors, or government programs) not already in the
list above. Focus on: food access, urban agriculture, youth education,
community wellness, and small nonprofit / community organization grants.
It's fine to return fewer than {count} if you can't find enough genuinely
new, real, current opportunities — never repeat or invent to hit the count.

Return ONLY the JSON array as specified.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )

    full_text = "".join(block.text for block in response.content if block.type == "text")
    cleaned = full_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").replace("json", "", 1).strip()

    try:
        new_funders = json.loads(cleaned)
    except json.JSONDecodeError:
        print("--- RAW MODEL OUTPUT (failed to parse) ---")
        print(full_text)
        raise

    return new_funders


def merge(existing: list[dict], new: list[dict]) -> list[dict]:
    existing_names_lower = {f["name"].strip().lower() for f in existing}
    deduped_new = [f for f in new if f["name"].strip().lower() not in existing_names_lower]
    return existing + deduped_new


if __name__ == "__main__":
    existing = load_existing()
    print(f"Already have {len(existing)} funders on file.")

    print("Researching new funders for A Farm For All...\n")
    new_funders = find_new_funders(AFFA_MISSION, existing, count=5)

    merged = merge(existing, new_funders)
    added = len(merged) - len(existing)

    print(f"Found {len(new_funders)} candidates, added {added} genuinely new leads:\n")
    for lead in new_funders:
        print(f"- [{lead['type']}] {lead['name']}")

    with open(FUNDERS_PATH, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"\nSaved. Total funders now: {len(merged)}")
