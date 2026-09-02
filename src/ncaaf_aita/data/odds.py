from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import pandas as pd

from ncaaf_aita.common import utc_now_iso
from ncaaf_aita.data.cache import RawSnapshotStore
from ncaaf_aita.data.http import HttpClient


APPROVED_SLATE = {"totals"}
APPROVED_DERIVATIVE = {"team_totals", "totals_h1"}


@dataclass
class QuotaPolicy:
    min_remaining: int = 100
    weekly_soft_budget: int = 90
    monthly_soft_budget: int = 400


class OddsQuotaBlocked(RuntimeError):
    pass


class OddsApiAdapter:
    def __init__(self, base: str, api_key: str, *, region: str = "us", bookmakers: list[str] | None = None,
                 ledger: str | Path = "data/diagnostics/ODDS_API_USAGE_LEDGER.csv", policy: QuotaPolicy | None = None,
                 http: HttpClient | None = None, store: RawSnapshotStore | None = None):
        if not api_key:
            raise ValueError("ODDS_API_KEY is required for market calls")
        self.base = base.rstrip("/")
        self.api_key = api_key
        self.region = region
        self.bookmakers = bookmakers or []
        self.ledger = Path(ledger)
        self.policy = policy or QuotaPolicy()
        self.http = http or HttpClient()
        self.store = store or RawSnapshotStore()
        self.last_remaining: int | None = None

    def _params(self, markets: Iterable[str] | None = None):
        p = {"apiKey": self.api_key, "oddsFormat": "american", "dateFormat": "iso"}
        if self.bookmakers:
            p["bookmakers"] = ",".join(self.bookmakers)
        else:
            p["regions"] = self.region
        if markets:
            p["markets"] = ",".join(markets)
        return p

    def _period_usage(self) -> tuple[int, int]:
        ledger = getattr(self, "ledger", None)
        if ledger is None or not ledger.exists():
            return 0, 0
        try:
            df = pd.read_csv(ledger)
            if df.empty or "timestamp" not in df or "cost_last" not in df:
                return 0, 0
            ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            cost = pd.to_numeric(df["cost_last"], errors="coerce").fillna(0)
            now = pd.Timestamp.now(tz="UTC")
            iso = now.isocalendar()
            weekly = int(cost[(ts.dt.isocalendar().year == iso.year) & (ts.dt.isocalendar().week == iso.week)].sum())
            monthly = int(cost[(ts.dt.year == now.year) & (ts.dt.month == now.month)].sum())
            return weekly, monthly
        except Exception:
            return 0, 0

    def _guard(self, projected_cost: int):
        weekly, monthly = self._period_usage()
        if weekly + projected_cost > self.policy.weekly_soft_budget:
            raise OddsQuotaBlocked(f"Charged odds call blocked by weekly budget: used={weekly}, projected={projected_cost}, budget={self.policy.weekly_soft_budget}")
        if monthly + projected_cost > self.policy.monthly_soft_budget:
            raise OddsQuotaBlocked(f"Charged odds call blocked by monthly budget: used={monthly}, projected={projected_cost}, budget={self.policy.monthly_soft_budget}")
        if self.last_remaining is not None and self.last_remaining - projected_cost < self.policy.min_remaining:
            raise OddsQuotaBlocked(f"Charged odds call blocked: remaining={self.last_remaining}, projected={projected_cost}, reserve={self.policy.min_remaining}")

    def _write_ledger(self, endpoint: str, markets: list[str], event_id: str | None, headers):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp": utc_now_iso(), "endpoint": endpoint, "sport": "americanfootball_ncaaf",
            "markets": ",".join(markets), "regions_bookmakers": ",".join(self.bookmakers) if self.bookmakers else self.region,
            "event_id": event_id or "", "cost_last": headers.get("x-requests-last", ""),
            "credits_used": headers.get("x-requests-used", ""), "credits_remaining": headers.get("x-requests-remaining", ""),
            "run_id": os.getenv("AITA_RUN_ID", ""),
        }
        exists = self.ledger.exists()
        with self.ledger.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(row))
            if not exists: w.writeheader()
            w.writerow(row)
        try: self.last_remaining = int(headers.get("x-requests-remaining"))
        except Exception: pass

    def events(self, sport: str = "americanfootball_ncaaf"):
        endpoint = f"sports/{sport}/events"
        r = self.http.get(f"{self.base}/{endpoint}", params={"apiKey": self.api_key, "dateFormat": "iso"})
        payload = r.json()
        self.store.save("odds_api", endpoint, {"dateFormat": "iso"}, payload, r.status_code)
        self._write_ledger(endpoint, [], None, r.headers)
        return payload

    def slate_totals(self, sport: str = "americanfootball_ncaaf"):
        markets = ["totals"]
        if self.last_remaining is None:
            self.events(sport)  # zero-quota call establishes current usage headers before spending credits
        self._guard(1)
        endpoint = f"sports/{sport}/odds"
        p = self._params(markets)
        r = self.http.get(f"{self.base}/{endpoint}", params=p)
        payload = r.json()
        self.store.save("odds_api", endpoint, {k: v for k, v in p.items() if k != "apiKey"}, payload, r.status_code)
        self._write_ledger(endpoint, markets, None, r.headers)
        return payload

    def event_derivatives(self, event_id: str, markets=("team_totals", "totals_h1"), sport: str = "americanfootball_ncaaf"):
        markets = list(markets)
        if self.last_remaining is None:
            self.events(sport)
        illegal = set(markets) - APPROVED_DERIVATIVE
        if illegal:
            raise ValueError(f"Unapproved V1 derivative markets: {sorted(illegal)}")
        self._guard(len(markets))
        endpoint = f"sports/{sport}/events/{event_id}/odds"
        p = self._params(markets)
        r = self.http.get(f"{self.base}/{endpoint}", params=p)
        payload = r.json()
        self.store.save("odds_api", endpoint, {k: v for k, v in p.items() if k != "apiKey"}, payload, r.status_code)
        self._write_ledger(endpoint, markets, event_id, r.headers)
        return payload

    @staticmethod
    def normalize(payload) -> pd.DataFrame:
        events = payload if isinstance(payload, list) else [payload]
        rows = []
        for ev in events:
            for book in ev.get("bookmakers", []) or []:
                for market in book.get("markets", []) or []:
                    key = market.get("key")
                    for o in market.get("outcomes", []) or []:
                        desc = o.get("description")
                        if key == "totals": family, period, team = "FG_TOTAL", "FG", None
                        elif key == "totals_h1": family, period, team = "H1_TOTAL", "H1", None
                        elif key == "team_totals": family, period, team = "TEAM_TOTAL", "FG", desc
                        else: continue
                        rows.append({
                            "odds_event_id": ev.get("id"), "home_team": ev.get("home_team"), "away_team": ev.get("away_team"),
                            "market_family": family, "period": period, "team_if_applicable": team,
                            "side": str(o.get("name", "")).upper(), "point": o.get("point"), "american_price": o.get("price"),
                            "bookmaker": book.get("key"), "bookmaker_title": book.get("title"),
                            "last_update": market.get("last_update") or book.get("last_update"), "snapshot_time": utc_now_iso(),
                        })
        return pd.DataFrame(rows)
