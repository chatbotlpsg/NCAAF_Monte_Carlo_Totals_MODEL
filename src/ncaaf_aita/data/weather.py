from __future__ import annotations

from datetime import datetime
from ncaaf_aita.data.cache import RawSnapshotStore
from ncaaf_aita.data.http import HttpClient


class OpenMeteoAdapter:
    HOURLY = "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m"

    def __init__(self, base: str, http: HttpClient | None = None, store: RawSnapshotStore | None = None):
        self.base = base
        self.http = http or HttpClient()
        self.store = store or RawSnapshotStore()

    def forecast(self, latitude: float, longitude: float, kickoff_iso: str):
        dt = datetime.fromisoformat(kickoff_iso.replace("Z", "+00:00"))
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": self.HOURLY,
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "UTC",
            "start_date": dt.date().isoformat(),
            "end_date": dt.date().isoformat(),
        }
        r = self.http.get(self.base, params=params)
        payload = r.json()
        self.store.save("open_meteo", "forecast", params, payload, r.status_code)
        times = payload.get("hourly", {}).get("time", [])
        if not times:
            return None
        target = dt.replace(minute=0, second=0, microsecond=0, tzinfo=None).isoformat(timespec="minutes")
        idx = min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]) - datetime.fromisoformat(target)))
        hourly = payload["hourly"]
        def v(key, default=None):
            vals = hourly.get(key, [])
            return vals[idx] if idx < len(vals) else default
        return {
            "temperature_f": v("temperature_2m"),
            "humidity": v("relative_humidity_2m"),
            "precip_probability": v("precipitation_probability"),
            "precip_amount": v("precipitation"),
            "weather_code": v("weather_code"),
            "wind_speed_mph": v("wind_speed_10m"),
            "wind_direction": v("wind_direction_10m"),
            "wind_gust_mph": v("wind_gusts_10m"),
        }
