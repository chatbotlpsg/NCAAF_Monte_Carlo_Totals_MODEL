from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from ncaaf_aita.common import sha256_file, write_json


REQUIRED = [
    "00_MANIFEST.json", "01_NCAAF_FINAL_BOARDS.md", "02_MASTER_EV_BOARD.csv", "03_FULL_GAME_TOTALS_BOARD.csv",
    "04_TEAM_TOTALS_BOARD.csv", "05_FIRST_HALF_TOTALS_BOARD.csv", "06_GAME_PROJECTIONS.csv",
    "07_MONTE_CARLO_DISTRIBUTIONS.csv", "08_MARKET_SNAPSHOT.csv", "09_MODEL_CONFIDENCE.csv",
    "10_EDGE_DRIVERS.csv", "11_CORRELATION_MATRIX.csv", "12_RISK_BOARD.csv", "13_DATA_QUALITY_REPORT.json",
    "14_MODEL_CARD.json", "15_RUN_AUDIT.json", "16_ODDS_API_USAGE_LEDGER.csv", "17_MC_CONVERGENCE_REPORT.csv", "18_FAIR_PRICE_CURVES.csv",
]


def validate_run_dir(run_dir: str | Path):
    d = Path(run_dir)
    missing = [f for f in REQUIRED if not (d/f).exists()]
    if missing:
        raise RuntimeError(f"HANDOFF_BLOCKED missing required files: {missing}")
    manifest = json.loads((d/"00_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("trading_agent_embedded") is not False:
        raise RuntimeError("HANDOFF_BLOCKED trading_agent_embedded must be false")
    return True


def finalize_manifest(run_dir: str | Path):
    d = Path(run_dir)
    manifest_path = d/"00_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = []
    for name in REQUIRED:
        if name == "00_MANIFEST.json": continue
        p = d/name
        files.append({"name": name, "sha256": sha256_file(p), "bytes": p.stat().st_size})
    manifest["files"] = files
    write_json(manifest_path, manifest)


def build_zip(run_dir: str | Path, zip_path: str | Path) -> Path:
    run_dir = Path(run_dir); zip_path = Path(zip_path)
    finalize_manifest(run_dir); validate_run_dir(run_dir)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    # Deterministic archive metadata: fixed timestamps and sorted members.
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(REQUIRED):
            data = (run_dir/name).read_bytes()
            info = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    return zip_path
