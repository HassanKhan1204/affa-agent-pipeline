"""
AFFA Partnership Agent — Step 2 prototype

What this does:
  Same pattern as funding_agent.py, but searches for potential PARTNER
  organizations instead of funders: schools, food-access orgs, healthcare
  organizations, restaurants, farmers markets, other nonprofits.

Run:
  python partnership_agent.py

Requires:
  pip install anthropic   (already installed if you ran funding_agent.py)
  ANTHROPIC_API_KEY already set as an environment variable
"""

import json
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env automatically

AFFA_MISSION = """
A Farm For All is a 501(c)(3) community farm working to expand access to land,
healthy food, agricultural education, microgreens, herbs, youth programming,
and community wellness.
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
Prefer organizations that are geographically plausible community partners
(local/regional) over large national chains, unless a national org has a
clear local-partnership program.
"""


def find_partners(mission: str, count: int = 15) -> list[dict]:
    user_prompt = f"""
Nonprofit mission:
{mission}

Research and return {count} real organizations that would make strong
community partners for this nonprofit. Look across these categories:
schools (especially those with garden/nutrition programs), other food-access
nonprofits, healthcare organizations focused on community health or
nutrition, restaurants interested in local sourcing, farmers markets, and
youth-serving community organizations.

Return ONLY the JSON array as specified.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )

    full_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    cleaned = full_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    try:
        partners = json.loads(cleaned)
    except json.JSONDecodeError:
        print("--- RAW MODEL OUTPUT (failed to parse) ---")
        print(full_text)
        raise

    return partners


if __name__ == "__main__":
    print("Researching potential partners for A Farm For All...\n")
    partners = find_partners(AFFA_MISSION, count=15)

    print(f"Found {len(partners)} leads:\n")
    for p in partners:
        print(f"- [{p['type']}] {p['name']}")
        print(f"  Focus: {p['focus_area']}")
        print(f"  Angle: {p['partnership_angle']}")
        print(f"  URL: {p.get('url', '')}\n")

    with open("partners.json", "w") as f:
        json.dump(partners, f, indent=2)
    print("Saved to partners.json")
