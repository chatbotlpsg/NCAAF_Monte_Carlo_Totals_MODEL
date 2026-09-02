from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from ncaaf_aita.common import sha256_bytes, utc_now_iso, write_json, slug, stable_json


class RawSnapshotStore:
    def __init__(self, root: str | Path = "data/raw"):
        self.root = Path(root)

    def save(self, provider: str, endpoint: str, params: dict[str, Any], payload: Any, http_status: int = 200,
             schema_version: str = "raw_v1") -> Path:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        digest = sha256_bytes(raw)
        stamp = utc_now_iso().replace(":", "-")
        folder = self.root / slug(provider) / slug(endpoint)
        folder.mkdir(parents=True, exist_ok=True)
        data_path = folder / f"{stamp}_{digest[:12]}.json"
        meta_path = folder / f"{stamp}_{digest[:12]}.meta.json"
        data_path.write_bytes(raw)
        write_json(meta_path, {
            "provider": provider,
            "endpoint": endpoint,
            "request_parameters": params,
            "retrieved_at_utc": utc_now_iso(),
            "http_status": http_status,
            "content_hash": digest,
            "schema_version": schema_version,
        })
        return data_path

    def find_latest(self, provider: str, endpoint: str, params: dict[str, Any]):
        folder = self.root / slug(provider) / slug(endpoint)
        if not folder.exists():
            return None
        target = stable_json(params)
        metas = sorted(folder.glob("*.meta.json"), reverse=True)
        for meta in metas:
            try:
                m = json.loads(meta.read_text(encoding="utf-8"))
                if stable_json(m.get("request_parameters", {})) != target:
                    continue
                data = Path(str(meta).replace(".meta.json", ".json"))
                if data.exists():
                    return json.loads(data.read_text(encoding="utf-8"))
            except Exception:
                continue
        return None
