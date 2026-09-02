from __future__ import annotations

from typing import Any
import pandas as pd
from ncaaf_aita.data.cache import RawSnapshotStore
from ncaaf_aita.data.http import HttpClient


class EspnSchemaDrift(RuntimeError):
    pass


class EspnAdapter:
    def __init__(self, base: str, http: HttpClient | None = None, store: RawSnapshotStore | None = None):
        self.base = base.rstrip("/")
        self.http = http or HttpClient()
        self.store = store or RawSnapshotStore()

    def _get(self, endpoint: str, params: dict[str, Any] | None = None):
        params = params or {}
        r = self.http.get(f"{self.base}/{endpoint.lstrip('/')}", params=params)
        payload = r.json()
        self.store.save("espn", endpoint, params, payload, r.status_code)
        return payload

    def scoreboard(self, date_yyyymmdd: str):
        data = self._get("scoreboard", {"dates": date_yyyymmdd, "limit": 300})
        if not isinstance(data.get("events"), list):
            raise EspnSchemaDrift("scoreboard.events missing or not a list")
        return data

    def summary(self, event_id: str):
        data = self._get("summary", {"event": event_id})
        if "header" not in data:
            raise EspnSchemaDrift("summary.header missing")
        return data

    def teams(self):
        return self._get("teams", {"limit": 500})

    def roster(self, team_id: str, season: int | None = None):
        data = self._get(f"teams/{team_id}/roster", {"season": season} if season is not None else {})
        if not any(k in data for k in ("athletes", "team")):
            raise EspnSchemaDrift("roster athlete/team structure missing")
        return data

    def team_schedule(self, team_id: str, season: int):
        return self._get(f"teams/{team_id}/schedule", {"season": season})


    @staticmethod
    def normalize_roster(data: dict[str, Any], team_id: str, season: int | None = None) -> pd.DataFrame:
        rows=[]
        groups=data.get("athletes") or []
        # ESPN roster payloads may group athletes by position or expose direct athlete objects.
        for g in groups:
            items=g.get("items") if isinstance(g,dict) else None
            if items is None:
                items=[g]
            for a in items or []:
                if not isinstance(a,dict): continue
                pos=a.get("position") or {}
                rows.append({
                    "espn_team_id":str(team_id),"season":season,"espn_athlete_id":str(a.get("id")) if a.get("id") is not None else None,
                    "player_name":a.get("fullName") or a.get("displayName"),"position":pos.get("abbreviation") or pos.get("name"),
                    "jersey":a.get("jersey"),"class":((a.get("experience") or {}).get("displayValue")),
                    "height":a.get("displayHeight"),"weight":a.get("displayWeight"),"active":a.get("active",True),
                })
        return pd.DataFrame(rows)

    @staticmethod
    def normalize_scoreboard(data: dict[str, Any]) -> pd.DataFrame:
        rows = []
        for event in data.get("events", []):
            comps = event.get("competitions") or []
            if not comps:
                continue
            comp = comps[0]
            competitors = comp.get("competitors") or []
            by_ha = {c.get("homeAway"): c for c in competitors}
            home, away = by_ha.get("home"), by_ha.get("away")
            if not home or not away:
                continue
            venue = (comp.get("venue") or {})
            status = ((event.get("status") or {}).get("type") or {}).get("name")
            rows.append({
                "espn_event_id": str(event.get("id")),
                "kickoff_utc": event.get("date"),
                "home_team": (home.get("team") or {}).get("displayName"),
                "away_team": (away.get("team") or {}).get("displayName"),
                # Stable school/location keys for the model layer. The display names
                # remain untouched for human-facing boards and sportsbook matching.
                "home_team_model": (home.get("team") or {}).get("location") or (home.get("team") or {}).get("shortDisplayName") or (home.get("team") or {}).get("displayName"),
                "away_team_model": (away.get("team") or {}).get("location") or (away.get("team") or {}).get("shortDisplayName") or (away.get("team") or {}).get("displayName"),
                "home_team_abbreviation": (home.get("team") or {}).get("abbreviation"),
                "away_team_abbreviation": (away.get("team") or {}).get("abbreviation"),
                "espn_home_team_id": str((home.get("team") or {}).get("id")),
                "espn_away_team_id": str((away.get("team") or {}).get("id")),
                "venue": venue.get("fullName"),
                "neutral_site": bool(comp.get("neutralSite", False)),
                "status": status,
            })
        return pd.DataFrame(rows)
