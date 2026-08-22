# A Farm For All — AI Growth Pipeline

A coordinated team of AI agents that researches funding, identifies partners,
builds a working CRM, and drafts personalized outreach — for
[A Farm For All](https://www.afarmforallnewyork.org/), a real 46-acre
nonprofit community farm in Webatuck, NY.

Built for the **A Farm For All Impact Track** at [hackathon name].

**Challenge:** How can a small community nonprofit use a team of AI agents
to operate with the capabilities of a much larger organization?

## What it does

```
Funding Agent  ─┐
                 ├──► funders.json ─┐
Partnership     ─┘   partners.json ─┼──► SQLite CRM ──► Outreach Agent ──► Campaign Agent
Agent                               │    (affa_crm.db)  (drafts emails)   (landing page)
                                     │
                                     └──► React CRM UI (searchable, filterable table)
```

| Agent | What it does |
|---|---|
| **Funding Agent** | Searches the web for real grants, foundations, and corporate sponsors that fit AFFA's mission |
| **Partnership Agent** | Searches for real schools, food-access nonprofits, healthcare orgs, and community groups as potential partners |
| **CRM builder** | Loads both lead lists into a single SQLite database |
| **Outreach Agent** | Drafts a short, specific outreach message for every lead — no templates, each one references the actual fit |
| **Campaign Agent** | Turns the CRM's real numbers into a one-page HTML campaign/landing page |
| **React CRM UI** | A searchable, filterable table view of every lead with expandable outreach drafts |

## Stack

- **Python** + **Anthropic API** (`claude-sonnet-4-6` with the `web_search` tool) for all agents
- **SQLite** for the CRM
- **React + Vite** for the CRM table UI
- Plain **HTML/CSS** for the static campaign page

No backend server, no Docker, no deployment — everything runs locally
against a single SQLite file, which keeps the whole pipeline reliable to
demo live.

## Running it

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY=your_key_here      # Windows: $env:ANTHROPIC_API_KEY="your_key_here"

# 2. Install the Python SDK
pip install anthropic

# 3. Run the pipeline in order
python funding_agent.py        # -> funders.json
python partnership_agent.py    # -> partners.json
python build_crm.py            # -> affa_crm.db
python outreach_agent.py       # fills in outreach_message for every lead
python campaign_agent.py       # -> affa_campaign.html

# 4. (Optional) Run the React CRM UI
python export_leads.py                       # -> leads.json
cp leads.json affa-ui/public/leads.json      # Windows: copy leads.json affa-ui\public\leads.json
cd affa-ui
npm install
npm run dev                                  # open the printed localhost URL
```

## Notes / limitations

- Web-search-grounded results are far more reliable than pure model recall,
  but should still be spot-checked before real-world outreach — the agents
  are told to omit anything they're not confident is real, but no LLM
  pipeline is 100% guaranteed accurate.
- Outreach messages are drafts meant for human review before sending, not
  an auto-send system.
- The React UI reads a static JSON export rather than a live database
  connection, by design — simpler and more demo-reliable than running a
  backend API server alongside the frontend.
