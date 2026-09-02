# NCAAF AITA Model — Windows Git Bash Install Commands

Assumption: `NCAAF_Monte_Carlo_Totals_MODEL_AITA_2026_V1.zip` has been moved to `C:/Python`.

## 1. Extract into the NCAAF model folder

```bash
cd /c/Python
if [ -d "NCAAF_Monte_Carlo_Totals_MODEL" ]; then
  mv "NCAAF_Monte_Carlo_Totals_MODEL" "NCAAF_Monte_Carlo_Totals_MODEL_BACKUP_$(date +%Y%m%d_%H%M%S)"
fi
mkdir -p "NCAAF_Monte_Carlo_Totals_MODEL"
unzip -q "NCAAF_Monte_Carlo_Totals_MODEL_AITA_2026_V1.zip" -d "NCAAF_Monte_Carlo_Totals_MODEL"
cd "NCAAF_Monte_Carlo_Totals_MODEL"
ls -la
```

## 2. Create/activate the Python environment

```bash
python -m venv virt
source virt/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

If `virt` already exists:

```bash
cd /c/Python/NCAAF_Monte_Carlo_Totals_MODEL
source virt/Scripts/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

## 3. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:

```text
CFBD_API_KEY=YOUR_CFBD_KEY
ODDS_API_KEY=YOUR_ODDS_API_KEY
```

Load keys in Git Bash:

```bash
set -a
source .env
set +a
```

## 4. Validate the installation

```bash
ncaaf-aita doctor
pytest -q
```

Expected release validation: `10 passed`.

## 5. Offline smoke test

```bash
ncaaf-aita demo --week 1 --slate-date 2026-09-05 --simulations 100000
```

## 6. Production sequence

```bash
ncaaf-aita discover-slate --date 2026-09-05

ncaaf-aita refresh-rosters \
  --season 2026 \
  --slate data/normalized/SLATE_EVENTS.csv

ncaaf-aita build-team-states --year 2026 --week 1

ncaaf-aita run \
  --season 2026 \
  --week 1 \
  --slate-date 2026-09-05 \
  --slate data/normalized/SLATE_EVENTS.csv \
  --team-states data/features/TEAM_STATES.csv \
  --stadiums data/normalized/STADIUMS.csv \
  --live-odds \
  --simulations 250000
```

The Python pipeline ends after generating the immutable external Trading-Agent handoff ZIP.

## 7. Optional 500,000-simulation verification

```bash
ncaaf-aita run \
  --season 2026 \
  --week 1 \
  --slate-date 2026-09-05 \
  --slate data/normalized/SLATE_EVENTS.csv \
  --team-states data/features/TEAM_STATES.csv \
  --stadiums data/normalized/STADIUMS.csv \
  --live-odds \
  --simulations 500000
```

## 8. Close proxy and post-slate audit

```bash
ncaaf-aita capture-close \
  --master-board outputs/handoffs/<RUN_DIRECTORY>/02_MASTER_EV_BOARD.csv \
  --label CLOSE_PROXY_PUBLIC

ncaaf-aita audit \
  --master-board outputs/handoffs/<RUN_DIRECTORY>/02_MASTER_EV_BOARD.csv \
  --results data/audits/RESULTS_2026_W01.csv \
  --close-snapshot data/snapshots/close/<CLOSE_PROXY_FILE>.csv \
  --out-dir data/audits/2026_W01
```
