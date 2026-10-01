# A Farm For All — AI Growth Pipeline

**🔗 [Live demo](https://affa-crm-ui.onrender.com/)** — the funder/partner
CRM, live. (Free-tier hosting: if it's been quiet, the first load can take
up to a minute to wake back up.)

A coordinated team of AI agents that researches funding, identifies partners,
builds a working CRM, and drafts personalized outreach — for
[A Farm For All](https://www.afarmforallnewyork.org/), a real 46-acre
nonprofit community farm in Webatuck, NY.

Built for the **A Farm For All Impact Track**.

**Challenge:** How can a small community nonprofit use a team of AI agents
to operate with the capabilities of a much larger organization?

## What it does

```
Funding Agent  ─┐
                 ├──► funders.json ─┐
Partnership     ─┘   partners.json ─┼──► SQLite CRM ──► Outreach Agent ──► Campaign Agent
Agent                               │    (affa_crm.db)  (drafts emails)   (landing page)
                                     │
                                     └──► load_data.py (ETL) ──► Postgres ──► FastAPI ──► React CRM UI
                                          (syncs leads, never          (CRM API)  (live table,
                                           overwrites human-set                   status editing)
                                           status)
```

| Agent | What it does |
|---|---|
| **Funding Agent** | Searches the web for real grants, foundations, and corporate sponsors that fit AFFA's mission |
| **Partnership Agent** | Searches for real schools, food-access nonprofits, healthcare orgs, and community groups as potential partners |
| **CRM builder** | Loads both lead lists into a single SQLite database |
| **Outreach Agent** | Drafts a short, specific outreach message for every lead — no templates, each one references the actual fit |
| **Campaign Agent** | Turns the CRM's real numbers into a one-page HTML campaign/landing page |
| **`load_data.py`** | Syncs SQLite's leads into Postgres (insert new leads, update everything except `status`, which is owned by the API/UI from that point on) |
| **FastAPI backend** | Serves the CRM over a real API (`/api/leads`, `/api/stats`) backed by Postgres, with a `PATCH` endpoint for updating a lead's status |
| **React CRM UI** | A searchable, filterable table view of every lead, with expandable outreach drafts and an inline status dropdown that writes back through the API |

## Stack

- **Python** + **Anthropic API** (`claude-sonnet-4-6` with the `web_search` tool) for all agents
- **SQLite** as the pipeline's working CRM (rebuilt fresh from `funders.json`/`partners.json` on every run)
- **FastAPI** + **SQLAlchemy** + **Postgres** as the serving layer the UI actually talks to, with a **pytest** suite (in-memory SQLite, no live DB needed to run it)
- **React + Vite** for the CRM table UI, built and served by **nginx** in Docker
- Plain **HTML/CSS** for the static campaign page
- **Docker + Docker Compose** to run the whole stack (pipeline, Postgres, API, UI) with one command

The pipeline itself still runs against a single SQLite file end to end,
which keeps it simple and reliable to demo. Its output is then synced into
Postgres, which is what the live API and UI actually read from — so the
CRM table stays up (and status edits stick) even while the pipeline is
mid-run or between runs.

## Running it

The whole thing is containerized, so the fastest path from clone to running
app doesn't require installing Python, Node, or any dependencies locally —
just Docker.

### Option A — Docker (recommended)

```bash
# 1. Add your key
cp .env.example .env
# edit .env and paste in your ANTHROPIC_API_KEY

# 2. Run the full pipeline (funding -> partnership -> CRM -> outreach ->
#    campaign -> export), end to end, in one command
docker compose run --rm pipeline

# 3. Start Postgres + the API, then sync the pipeline's SQLite output into it
docker compose up -d db backend
docker compose run --rm backend python load_data.py

# 4. Serve the CRM table UI at http://localhost:8080
docker compose up --build ui
```

The API is now live at `http://localhost:8001` (`/api/leads`, `/api/stats`,
interactive docs at `/docs`), and the UI at `http://localhost:8080` talks to
it directly — including the status dropdown on each row, which writes
straight back to Postgres. (The API listens on port 8000 *inside* Docker's
network — that's what the UI container actually talks to — it's just
published on your machine as 8001, since 8000 is a common port for other
local dev servers to already be using.)

Re-run a single pipeline step instead of the whole thing with
`docker compose run --rm pipeline python funding_agent.py` (swap in any
script name). Nothing is lost between runs — the repo is bind-mounted into
the container, so `affa_crm.db`, `leads.json`, and `docs/index.html` are
written straight back onto your machine. After any pipeline re-run, repeat
step 3's `load_data.py` sync to pick up new leads — it only ever adds or
refreshes lead details, and never touches a status you've already set by
hand in the UI.

Run the backend's test suite (no Postgres needed — it uses an in-memory
SQLite DB) with:

```bash
docker compose run --rm backend sh -c "pip install -r requirements-dev.txt && pytest"
```

### Option B — run it natively

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY=your_key_here      # Windows: $env:ANTHROPIC_API_KEY="your_key_here"

# 2. Install the Python SDK
pip install -r requirements.txt

# 3. Run the pipeline in order (or just ./run_pipeline.sh to do all of this)
python funding_agent.py        # -> funders.json
python partnership_agent.py    # -> partners.json
python build_crm.py            # -> affa_crm.db
python outreach_agent.py       # fills in outreach_message for every lead
python campaign_agent.py       # -> docs/index.html

# 4. (Optional) Run the API + React CRM UI
cd backend
pip install -r requirements.txt
python load_data.py --source ../affa_crm.db   # syncs affa_crm.db -> a local SQLite API DB
uvicorn app.main:app --reload                 # API at http://localhost:8000

# in a second terminal
cd affa-ui
npm install
npm run dev                                   # open the printed localhost URL
```

Without a `DATABASE_URL` set, the backend falls back to its own local
SQLite file (`backend/affa_api.db`) instead of Postgres — handy for running
natively without installing a database server.

## Automatic daily updates

This repo runs itself. A GitHub Actions workflow
(`.github/workflows/daily-update.yml`) runs the full pipeline every day,
finds new funders and partners (skipping anything already found), and
publishes a refreshed campaign page via GitHub Pages — no laptop required.

**One-time setup:**

1. **Add your API key as a secret** — repo Settings → Secrets and variables
   → Actions → New repository secret → name it `ANTHROPIC_API_KEY`, paste
   your key as the value.
2. **Enable GitHub Pages** — repo Settings → Pages → Source: "Deploy from a
   branch" → Branch: `main`, folder: `/docs` → Save. Your live page will be
   at `https://<username>.github.io/<repo-name>/`.
3. **(Optional) Trigger it manually the first time** — Actions tab → "Daily
   AFFA Pipeline Update" → Run workflow, instead of waiting for the next
   scheduled run.

After that, it runs daily on its own, growing the lead list and
re-publishing the page automatically. Add the `PRODUCTION_DATABASE_URL`
secret described below and this same workflow also keeps a live, deployed
CRM in sync — no separate cron job needed.

## Deploying it live

Everything above runs against a database only your machine can see. To get
a link anyone can open — coworkers, recruiters, teammates on their own
devices — host the database on **Neon** (Postgres, free tier that never
expires) and the API + UI on **Render** (free tier; the `render.yaml` in
this repo deploys both services in one step). Total cost: $0, no credit
card required for either service.

**1. Create the database (Neon)**

1. Go to [neon.com](https://neon.com) and sign up.
2. Create a new project (any name/region is fine).
3. On the project dashboard, copy the **connection string** — it looks like
   `postgresql://<user>:<password>@<host>/<database>?sslmode=require`. Keep
   this handy for the next two steps.

**2. Deploy the API + UI (Render)**

1. Go to [render.com](https://render.com) and sign up.
2. Dashboard → **New** → **Blueprint** → connect your GitHub account →
   select the `affa-agent-pipeline` repo.
3. Render reads `render.yaml` and proposes two services: `affa-crm-backend`
   (the API) and `affa-crm-ui` (the table). When it prompts for
   `DATABASE_URL`, paste in the Neon connection string from step 1.
4. Click **Deploy Blueprint**. Both services build — the UI runs
   `npm run build`, the backend builds its Docker image — first deploy
   takes a few minutes.
5. The database starts out empty. From your own machine, load it once:
   ```bash
   cd backend
   pip install -r requirements.txt
   # macOS/Linux:
   DATABASE_URL="<paste the Neon connection string>" python load_data.py --source ../affa_crm.db
   # Windows PowerShell:
   $env:DATABASE_URL="<paste the Neon connection string>"; python load_data.py --source ../affa_crm.db
   ```
   This creates the `leads` table and loads whatever's currently in your
   local `affa_crm.db`.
6. Visit `https://affa-crm-ui.onrender.com` — that's the shareable link.

**3. Keep the live site in sync automatically**

The daily pipeline workflow can push straight into this same database, so
new leads show up on the live site with no manual steps:

1. Repo **Settings** → **Secrets and variables** → **Actions** → **New
   repository secret**.
2. Name it `PRODUCTION_DATABASE_URL`, paste the same Neon connection string
   as the value.

From the next scheduled run onward — or trigger it now from the **Actions**
tab — new funders and partners reach the live site automatically.

**Worth knowing:**

- Both Render's free web service and Neon's free database "sleep" after a
  few minutes of inactivity. The first visit after a quiet stretch takes
  30-60 seconds to wake back up; after that it's normal speed. That's
  expected free-tier behavior, not a bug — the updated error message in the
  UI explains this if someone hits it mid-wakeup.
- The two service names in `render.yaml` (`affa-crm-backend`,
  `affa-crm-ui`) double as their URLs. If Render had to rename either one
  (only happens if that name was already taken), update `CORS_ORIGINS` on
  the backend and `VITE_API_BASE` on the UI in the Render dashboard to
  match the real URL, then trigger a manual redeploy of both.
- A status change made through the live UI writes straight to Neon — same
  API code path as the local Docker setup, just a different database.

## Notes / limitations

- Web-search-grounded results are far more reliable than pure model recall,
  but should still be spot-checked before real-world outreach — the agents
  are told to omit anything they're not confident is real, but no LLM
  pipeline is 100% guaranteed accurate.
- Outreach messages are drafts meant for human review before sending, not
  an auto-send system.
- The daily GitHub Actions workflow always commits `leads.json` as a static
  snapshot (used by the static campaign page). It only pushes into a live
  Postgres database if the `PRODUCTION_DATABASE_URL` secret is set — see
  "Deploying it live" above; without it, that step is a harmless no-op.
