#!/usr/bin/env bash
# Runs the full AFFA agent pipeline end to end, in the same order described
# in the README, and copies the result into affa-ui/public so the React UI
# picks it up immediately. Safe to re-run — every step is idempotent.
#
# Usage:
#   ./run_pipeline.sh              # run everything
#   docker compose run pipeline    # same, inside Docker

set -euo pipefail

: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY must be set (see .env.example)}"

echo "==> [1/6] Funding agent"
python funding_agent.py

echo "==> [2/6] Partnership agent"
python partnership_agent.py

echo "==> [3/6] Build CRM"
python build_crm.py

echo "==> [4/6] Outreach agent"
python outreach_agent.py

echo "==> [5/6] Campaign agent"
python campaign_agent.py

echo "==> [6/6] Export leads for the React UI"
python export_leads.py
mkdir -p affa-ui/public
cp leads.json affa-ui/public/leads.json

echo
echo "Pipeline complete. affa_crm.db, leads.json, and docs/index.html are up to date."
echo "Run the UI with: docker compose up ui   (or: cd affa-ui && npm run dev)"
