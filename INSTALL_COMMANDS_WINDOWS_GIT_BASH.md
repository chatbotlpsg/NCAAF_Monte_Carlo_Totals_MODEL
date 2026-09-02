# NCAAF AITA V1.1 — Windows Git Bash Replacement + Run Commands

## Replace the prior codebase

Assumption: `NCAAF_Monte_Carlo_Totals_MODEL_AITA_2026_V1.1.0_ALL_GAME_BOARDS_FIX.zip` is in `C:/Python`.

```bash
cd /c/Python

mv \
  NCAAF_Monte_Carlo_Totals_MODEL \
  NCAAF_Monte_Carlo_Totals_MODEL_PRE_V1_1_FIX

mkdir -p /c/Python/_NCAAF_V1_1_EXTRACT

unzip -q \
  NCAAF_Monte_Carlo_Totals_MODEL_AITA_2026_V1.1.0_ALL_GAME_BOARDS_FIX.zip \
  -d /c/Python/_NCAAF_V1_1_EXTRACT

mv \
  /c/Python/_NCAAF_V1_1_EXTRACT/NCAAF_Monte_Carlo_Totals_MODEL_AITA_2026_V1.1.0 \
  /c/Python/NCAAF_Monte_Carlo_Totals_MODEL

cd /c/Python/NCAAF_Monte_Carlo_Totals_MODEL
```

## Restore secrets and local registries

```bash
cp \
  /c/Python/NCAAF_Monte_Carlo_Totals_MODEL_PRE_V1_1_FIX/.env \
  .env
```

If you populated the stadium/QB files previously, preserve them:

```bash
cp \
  /c/Python/NCAAF_Monte_Carlo_Totals_MODEL_PRE_V1_1_FIX/data/normalized/STADIUMS.csv \
  data/normalized/STADIUMS.csv

cp \
  /c/Python/NCAAF_Monte_Carlo_Totals_MODEL_PRE_V1_1_FIX/data/features/STARTER_QB_MAP.csv \
  data/features/STARTER_QB_MAP.csv
```

## Create environment

```bash
python -m venv virt
source virt/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Load `.env`:

```bash
set -a
source .env
set +a
```

Validate:

```bash
ncaaf-aita doctor
python -m pytest -q
```

Expected: `15 passed`.

## September 3, 2026 production run

**Rediscover the slate after installing V1.1.** This is mandatory because the normalized slate now stores separate ESPN display names and canonical model/location names.

```bash
ncaaf-aita discover-slate \
  --date 2026-09-03
```

Inspect identity fields:

```bash
python - <<'PY'
import pandas as pd

df = pd.read_csv("data/normalized/SLATE_EVENTS.csv")
print(df[[
    "away_team","away_team_model",
    "home_team","home_team_model",
    "odds_event_id","market_mapping_status"
]].to_string(index=False))
PY
```

Refresh rosters:

```bash
ncaaf-aita refresh-rosters \
  --season 2026 \
  --slate data/normalized/SLATE_EVENTS.csv
```

Build Week 1 states:

```bash
ncaaf-aita build-team-states \
  --year 2026 \
  --week 1
```

Run one final-board production pass:

```bash
ncaaf-aita run \
  --season 2026 \
  --week 1 \
  --slate-date 2026-09-03 \
  --slate data/normalized/SLATE_EVENTS.csv \
  --team-states data/features/TEAM_STATES.csv \
  --stadiums data/normalized/STADIUMS.csv \
  --live-odds \
  --simulations 250000
```

## Locate and validate the Trading-Agent handoff

```bash
LATEST_ZIP=$(ls -t \
  outputs/handoffs/NCAAF_MONTE_TOTALS_2026_W01_TRADING_AGENT_HANDOFF_*.zip \
  | head -1)

echo "$LATEST_ZIP"
unzip -t "$LATEST_ZIP"
sha256sum "$LATEST_ZIP"
```

Resolve the run directory:

```bash
RUN_ID=$(basename "$LATEST_ZIP" .zip | sed 's/.*_HANDOFF_//')
RUN_DIR="outputs/handoffs/NCAAF_2026_W01_${RUN_ID}"

echo "$RUN_DIR"
```

Validate the all-game boards and EV separation:

```bash
python - <<PY
import json
import pandas as pd
from pathlib import Path

r = Path("${RUN_DIR}")
m = json.loads((r / "00_MANIFEST.json").read_text())

print("DATA QUALITY:", m["data_quality_status"])
print("MODEL COVERAGE:", m["model_coverage"])
print("CALIBRATION:", m["calibration_status"])
print("EV STATUS:", m["ev_estimate_status"])

for name in [
    "03_FULL_GAME_TOTALS_BOARD.csv",
    "04_TEAM_TOTALS_BOARD.csv",
    "05_FIRST_HALF_TOTALS_BOARD.csv",
    "02_MASTER_EV_BOARD.csv",
    "06_GAME_PROJECTIONS.csv",
]:
    df = pd.read_csv(r / name)
    print(name, "ROWS=", len(df))
PY
```

For an 11-game slate the expected model coverage shape is:

```text
03_FULL_GAME_TOTALS_BOARD.csv  = 11 rows
04_TEAM_TOTALS_BOARD.csv       = 22 rows
05_FIRST_HALF_TOTALS_BOARD.csv = 11 rows
06_GAME_PROJECTIONS.csv        = 11 rows
```

`02_MASTER_EV_BOARD.csv` may have more/fewer rows depending on exact sportsbook market coverage. It must never fabricate EV for an unpriced game.

## Feed the ZIP to the external Trading Agent

```bash
mkdir -p /c/Python/NCAAF_TRADING_AGENT_HANDOFFS/2026-09-03

cp "$LATEST_ZIP" \
  /c/Python/NCAAF_TRADING_AGENT_HANDOFFS/2026-09-03/

cp "$LATEST_ZIP" \
  /c/Python/NCAAF_TRADING_AGENT_HANDOFFS/2026-09-03/NCAAF_2026-09-03_WEEK1_TRADING_AGENT_HANDOFF.zip

unzip -t \
  /c/Python/NCAAF_TRADING_AGENT_HANDOFFS/2026-09-03/NCAAF_2026-09-03_WEEK1_TRADING_AGENT_HANDOFF.zip
```

Final Trading-Agent input:

```text
C:\Python\NCAAF_TRADING_AGENT_HANDOFFS\2026-09-03\NCAAF_2026-09-03_WEEK1_TRADING_AGENT_HANDOFF.zip
```

**STOP PYTHON THERE.** The external Trading Agent owns final actionability, close capture, grading, CLV/ROI and the post-slate recap/audit history.
