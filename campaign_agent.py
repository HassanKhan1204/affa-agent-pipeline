"""
AFFA Campaign Agent — Step 4: turn the CRM into a one-page campaign

What this does:
  Reads affa_crm.db (built by build_crm.py + outreach_agent.py), pulls
  real numbers and sample leads, asks Claude to write short campaign copy
  (headline, subhead, impact lines, pitch paragraph), then renders it all
  into a single static HTML landing page you can open in a browser or
  screen-share during your demo.

Run:
  python campaign_agent.py

Requires:
  affa_crm.db already populated (run build_crm.py + outreach_agent.py first)
  ANTHROPIC_API_KEY already set as an environment variable

Output:
  affa_campaign.html — open it directly in any browser
"""

import json
import sqlite3
from anthropic import Anthropic

client = Anthropic()

DB_PATH = "affa_crm.db"
OUTPUT_PATH = "affa_campaign.html"

SYSTEM_PROMPT = """You write short campaign copy for a small nonprofit
community farm's landing page. You are given real numbers and real
example leads (funders and partners) researched by their AI agent
pipeline. Write copy that is specific, confident, and warm — never
corporate, never vague.

Respond with ONLY a JSON object (no markdown fences, no preamble) with
this exact shape:

{
  "headline": "string - 4-8 words, punchy, specific to this pipeline's result",
  "subhead": "string - 1 sentence expanding on the headline",
  "pitch": "string - 2-3 sentences, the core narrative: how a small farm used a coordinated agent system to operate like a much larger organization",
  "impact_lines": ["string", "string", "string"]  // exactly 3 short (5-9 word) stat-driven lines
}
"""


def get_stats_and_leads(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    funders = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE category = 'funder'"
    ).fetchone()[0]
    partners = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE category = 'partner'"
    ).fetchone()[0]
    drafted = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE outreach_message IS NOT NULL AND outreach_message != ''"
    ).fetchone()[0]

    sample_leads = conn.execute(
        """SELECT name, category, subtype, focus_area
           FROM leads ORDER BY RANDOM() LIMIT 6"""
    ).fetchall()

    all_leads = conn.execute(
        """SELECT name, category, subtype, focus_area, url
           FROM leads ORDER BY category, name"""
    ).fetchall()

    return {
        "total": total,
        "funders": funders,
        "partners": partners,
        "drafted": drafted,
        "sample_leads": sample_leads,
        "all_leads": all_leads,
    }


def generate_copy(stats: dict) -> dict:
    sample_text = "\n".join(
        f"- [{row[1]}] {row[0]} ({row[3]})" for row in stats["sample_leads"]
    )

    user_prompt = f"""
Pipeline results for A Farm For All (a small community farm nonprofit):
- {stats['funders']} funders researched
- {stats['partners']} potential community partners identified
- {stats['drafted']} personalized outreach messages drafted
- {stats['total']} total leads now in a working CRM

Example leads the agents found:
{sample_text}

Write the campaign copy now.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json", "", 1).strip()

    return json.loads(text)


def render_html(copy: dict, stats: dict) -> str:
    lead_rows = "\n".join(
        f"""
        <tr>
          <td>{name}</td>
          <td><span class="tag tag-{category}">{category}</span></td>
          <td>{subtype or ''}</td>
          <td>{focus_area}</td>
        </tr>"""
        for name, category, subtype, focus_area, url in stats["all_leads"]
    )

    impact_html = "\n".join(
        f'<li><span class="sprout">↟</span>{line}</li>'
        for line in copy["impact_lines"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A Farm For All — Growth Pipeline</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --soil: #2C2418;
    --paper: #F7F4EC;
    --sage: #5C7A5C;
    --sage-dark: #3E5940;
    --butter: #E8B84B;
    --line: #DCD5C2;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--paper);
    color: var(--soil);
    font-family: 'Public Sans', sans-serif;
    line-height: 1.5;
  }}

  .hero {{
    background: var(--soil);
    color: var(--paper);
    padding: 5rem 2rem 4rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}

  .hero::before {{
    content: "";
    position: absolute;
    top: -40%;
    right: -10%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, var(--sage) 0%, transparent 70%);
    opacity: 0.25;
  }}

  .eyebrow {{
    font-size: 0.8rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--butter);
    font-weight: 600;
    position: relative;
  }}

  h1 {{
    font-family: 'Fraunces', serif;
    font-size: clamp(2.2rem, 5vw, 3.6rem);
    font-weight: 700;
    margin: 1rem auto 1.2rem;
    max-width: 800px;
    position: relative;
  }}

  .subhead {{
    font-size: 1.15rem;
    color: #D8D2C0;
    max-width: 600px;
    margin: 0 auto;
    position: relative;
  }}

  .stats-bar {{
    display: flex;
    justify-content: center;
    gap: 3rem;
    flex-wrap: wrap;
    background: var(--sage-dark);
    padding: 2rem;
  }}

  .stat {{ text-align: center; color: var(--paper); }}
  .stat .num {{
    font-family: 'Fraunces', serif;
    font-size: 2.4rem;
    font-weight: 700;
    display: block;
  }}
  .stat .label {{
    font-size: 0.8rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #C9DCC9;
  }}

  main {{ max-width: 900px; margin: 0 auto; padding: 3.5rem 2rem; }}

  .pitch {{
    font-size: 1.25rem;
    font-family: 'Fraunces', serif;
    font-weight: 400;
    line-height: 1.6;
    color: var(--soil);
    border-left: 3px solid var(--sage);
    padding-left: 1.5rem;
    margin-bottom: 3rem;
  }}

  .impact-list {{
    list-style: none;
    display: grid;
    gap: 0.9rem;
    margin-bottom: 3.5rem;
  }}

  .impact-list li {{
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 1.05rem;
    font-weight: 500;
  }}

  .sprout {{
    color: var(--sage);
    font-size: 1.2rem;
    font-weight: 700;
  }}

  h2 {{
    font-family: 'Fraunces', serif;
    font-size: 1.5rem;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.8rem;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
  }}

  th {{
    text-align: left;
    padding: 0.6rem 0.8rem;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #7A7461;
    border-bottom: 1px solid var(--line);
  }}

  td {{
    padding: 0.7rem 0.8rem;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }}

  .tag {{
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: capitalize;
  }}

  .tag-funder {{ background: #E8B84B33; color: #8A6414; }}
  .tag-partner {{ background: #5C7A5C33; color: var(--sage-dark); }}

  footer {{
    text-align: center;
    padding: 2.5rem;
    color: #8A8266;
    font-size: 0.85rem;
  }}
</style>
</head>
<body>

  <section class="hero">
    <div class="eyebrow">A Farm For All &middot; Growth Pipeline</div>
    <h1>{copy['headline']}</h1>
    <p class="subhead">{copy['subhead']}</p>
  </section>

  <div class="stats-bar">
    <div class="stat"><span class="num">{stats['funders']}</span><span class="label">Funders Found</span></div>
    <div class="stat"><span class="num">{stats['partners']}</span><span class="label">Partners Identified</span></div>
    <div class="stat"><span class="num">{stats['drafted']}</span><span class="label">Messages Drafted</span></div>
    <div class="stat"><span class="num">{stats['total']}</span><span class="label">Leads in CRM</span></div>
  </div>

  <main>
    <p class="pitch">{copy['pitch']}</p>

    <ul class="impact-list">
      {impact_html}
    </ul>

    <h2>Full Pipeline Results</h2>
    <table>
      <thead>
        <tr><th>Organization</th><th>Category</th><th>Type</th><th>Focus Area</th></tr>
      </thead>
      <tbody>
        {lead_rows}
      </tbody>
    </table>
  </main>

  <footer>Built by a coordinated team of AI agents for A Farm For All.</footer>

</body>
</html>
"""


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    stats = get_stats_and_leads(conn)
    conn.close()

    print(f"Pulled {stats['total']} leads from CRM. Generating campaign copy...")
    copy = generate_copy(stats)

    print(f"\nHeadline: {copy['headline']}")
    print(f"Subhead: {copy['subhead']}\n")

    html = render_html(copy, stats)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved campaign page to {OUTPUT_PATH} — open it in your browser.")
