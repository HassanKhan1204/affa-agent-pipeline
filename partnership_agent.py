"""
AFFA Partnership Agent — with daily dedup support

Same dedup pattern as funding_agent.py, but for potential community
partners instead of funders.

Run:
  python partnership_agent.py
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
to find REAL, currently operating organizations that could become community
PARTNERS for the nonprofit — not funders, but collaborators: schools,
other nonprofits, food-access organizations, healthcare organizations,
restaurants, farmers markets, and community organizations.

After researching, respond with ONLY a JSON array (no markdown fences, no
preamble, no commentary) where each item has this exact shape:

{
  "name": "string - name of the organization",
  "type": "school | nonprofit | healthcare | restaurant | farmers_market | community_org",
  "focus_area": "string - what they do",
  "partnership_angle": "string - 1 sentence on what a partnership with A Farm For All could look like",
  "url": "string - link if found, else empty string"
}

Only include real organizations you found through search. If you are not
confident something is real and current, leave it out rather than guessing.
Strongly prefer organizations located in or serving Dutchess County NY,
the wider Hudson Valley, western Connecticut, or New York City boroughs
(especially the Bronx and other under-served urban neighborhoods) over
generic national organizations with no clear local presence. A national
org is only acceptable if it has a specific chapter, office, or program
operating in this region.

Do NOT include any organization already in the "already found" list you're
given — every result must be new.
"""

PARTNERS_PATH = "partners.json"


def load_existing() -> list[dict]:
    if os.path.exists(PARTNERS_PATH):
        with open(PARTNERS_PATH, "r") as f:
            return json.load(f)
    return []


def find_new_partners(mission: str, existing: list[dict], count: int = 5) -> list[dict]:
    existing_names = [p["name"] for p in existing]
    existing_list_text = "\n".join(f"- {name}" for name in existing_names) or "(none yet)"

    user_prompt = f"""
Nonprofit mission:
{mission}

We already have these partners in our list — do NOT repeat any of them:
{existing_list_text}

Research and return {count} NEW real organizations that would make strong
community partners for this nonprofit, not already in the list above. Look
across these categories: schools (especially those with garden/nutrition
programs), other food-access nonprofits, healthcare organizations focused
on community health or nutrition, restaurants interested in local sourcing,
farmers markets, and youth-serving community organizations. It's fine to
return fewer than {count} if you can't find enough genuinely new, real,
current organizations — never repeat or invent to hit the count.

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
        new_partners = json.loads(cleaned)
    except json.JSONDecodeError:
        print("--- RAW MODEL OUTPUT (failed to parse) ---")
        print(full_text)
        raise

    return new_partners


def merge(existing: list[dict], new: list[dict]) -> list[dict]:
    existing_names_lower = {p["name"].strip().lower() for p in existing}
    deduped_new = [p for p in new if p["name"].strip().lower() not in existing_names_lower]
    return existing + deduped_new


if __name__ == "__main__":
    existing = load_existing()
    print(f"Already have {len(existing)} partners on file.")

    print("Researching new partners for A Farm For All...\n")
    new_partners = find_new_partners(AFFA_MISSION, existing, count=5)

    merged = merge(existing, new_partners)
    added = len(merged) - len(existing)

    print(f"Found {len(new_partners)} candidates, added {added} genuinely new leads:\n")
    for lead in new_partners:
        print(f"- [{lead['type']}] {lead['name']}")

    with open(PARTNERS_PATH, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"\nSaved. Total partners now: {len(merged)}")
