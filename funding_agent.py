"""
AFFA Funding Agent — Step 1 prototype

What this does:
  Calls Claude with the web_search tool, asks it to research real grants /
  foundations / corporate sponsors relevant to "A Farm For All," and returns
  a clean JSON list of leads.

Run:
  python funding_agent.py

Requires:
  pip install anthropic
  export ANTHROPIC_API_KEY=your_key_here   (Windows: set ANTHROPIC_API_KEY=your_key_here)
"""

import json
import os
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env automatically

AFFA_MISSION = """
A Farm For All is a 501(c)(3) community farm working to expand access to land,
healthy food, agricultural education, microgreens, herbs, youth programming,
and community wellness.
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
guessing.
"""


def find_funders(mission: str, count: int = 15) -> list[dict]:
    user_prompt = f"""
Nonprofit mission:
{mission}

Research and return {count} real funding opportunities (grants, foundations,
corporate sponsors, or government programs) that would plausibly fund this
organization. Focus on: food access, urban agriculture, youth education,
community wellness, and small nonprofit / community organization grants.

Return ONLY the JSON array as specified.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )

    # Collect all text blocks (search results may interleave with text)
    full_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    # Clean up in case the model wraps it in ```json fences anyway
    cleaned = full_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    try:
        leads = json.loads(cleaned)
    except json.JSONDecodeError:
        print("--- RAW MODEL OUTPUT (failed to parse) ---")
        print(full_text)
        raise

    return leads


if __name__ == "__main__":
    print("Researching funders for A Farm For All...\n")
    leads = find_funders(AFFA_MISSION, count=15)

    print(f"Found {len(leads)} leads:\n")
    for lead in leads:
        print(f"- [{lead['type']}] {lead['name']}")
        print(f"  Focus: {lead['focus_area']}")
        print(f"  Fit: {lead['fit_reason']}")
        print(f"  URL: {lead.get('url', '')}\n")

    # Save to file so the CRM step can read it later
    with open("funders.json", "w") as f:
        json.dump(leads, f, indent=2)
    print("Saved to funders.json")
