from __future__ import annotations

import time
import httpx


class HttpClient:
    def __init__(self, timeout: float = 30.0, min_interval: float = 0.20, retries: int = 3):
        self.client = httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "AITA-NCAAF/1.0"})
        self.min_interval = min_interval
        self.retries = retries
        self._last = 0.0

    def get(self, url: str, *, params=None, headers=None) -> httpx.Response:
        err = None
        for i in range(self.retries):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            try:
                r = self.client.get(url, params=params, headers=headers)
                self._last = time.monotonic()
                if r.status_code in (429, 500, 502, 503, 504) and i + 1 < self.retries:
                    time.sleep(0.5 * (2 ** i))
                    continue
                r.raise_for_status()
                return r
            except Exception as exc:
                err = exc
                if i + 1 < self.retries:
                    time.sleep(0.5 * (2 ** i))
        raise RuntimeError(f"HTTP GET failed for {url}: {err}")
