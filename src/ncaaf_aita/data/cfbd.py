from __future__ import annotations

from typing import Any
from ncaaf_aita.data.cache import RawSnapshotStore
from ncaaf_aita.data.http import HttpClient


class CfbdAdapter:
    def __init__(self, base: str, api_key: str, http: HttpClient | None = None, store: RawSnapshotStore | None = None):
        if not api_key:
            raise ValueError("CFBD_API_KEY is required for CFBD calls")
        self.base = base.rstrip("/")
        self.api_key = api_key
        self.http = http or HttpClient(min_interval=0.35)
        self.store = store or RawSnapshotStore()

    def _get(self, endpoint: str, params: dict[str, Any], *, use_cache: bool = False):
        if use_cache:
            cached = self.store.find_latest("cfbd", endpoint, params)
            if cached is not None:
                return cached
        headers = {"Authorization": f"Bearer {self.api_key}"}
        r = self.http.get(f"{self.base}/{endpoint.lstrip('/')}", params=params, headers=headers)
        payload = r.json()
        self.store.save("cfbd", endpoint, params, payload, r.status_code)
        return payload

    def games(self, year: int, week: int | None = None, team: str | None = None):
        p = {"year": year}
        if week is not None: p["week"] = week
        if team: p["team"] = team
        return self._get("games", p)

    def plays(self, year: int, week: int, classification: str = "fbs"):
        return self._get("plays", {"year": year, "week": week, "seasonType": "regular", "classification": classification}, use_cache=True)

    def core_ratings(self, year: int):
        return self._get("ratings/core", {"year": year})

    def sp_ratings(self, year: int):
        return self._get("ratings/sp", {"year": year})

    def srs_ratings(self, year: int):
        return self._get("ratings/srs", {"year": year})

    def elo_ratings(self, year: int, week: int | None = None):
        p = {"year": year}
        if week is not None: p["week"] = week
        return self._get("ratings/elo", p)

    def recruiting_teams(self, year: int):
        return self._get("recruiting/teams", {"year": year})
