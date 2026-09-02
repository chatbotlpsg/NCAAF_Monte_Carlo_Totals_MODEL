#!/usr/bin/env bash
set -euo pipefail
SEASON=${1:-2026}
WEEK=${2:-1}
SLATE_DATE=${3:-2026-09-05}
python -m ncaaf_aita.cli run \
  --season "$SEASON" --week "$WEEK" --slate-date "$SLATE_DATE" \
  --slate data/normalized/SLATE_EVENTS.csv \
  --team-states data/features/TEAM_STATES.csv \
  --live-odds
