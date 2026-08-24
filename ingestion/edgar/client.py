"""Low-level HTTP client for SEC EDGAR.

SEC requires every request to carry an identifying `User-Agent: name email`
header, and asks that callers stay under ~10 requests/second. This module
centralizes both rules so every other module in `ingestion.edgar` gets them
for free instead of re-implementing them.
"""

import time

import httpx

from config import settings

# --- Rate limiting ---
# SEC's fair-access guidance caps automated access at 10 req/sec. We sleep a
# fixed interval after every request rather than tracking a rolling window,
# which is simpler and comfortably under the limit for our use case (a few
# tickers, a handful of filings each).
MIN_REQUEST_INTERVAL_SECONDS = 0.2


class EdgarClient:
    """Thin wrapper around httpx.Client with SEC's required headers + rate limit."""

    def __init__(self) -> None:
        # SEC rejects requests without a descriptive User-Agent, so we build
        # it from the typed config (Settings.sec_edgar_user_agent) rather
        # than hardcoding it here.
        headers = {"User-Agent": settings.sec_edgar_user_agent}
        self._http = httpx.Client(headers=headers, timeout=30.0)
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        """Sleep just enough to keep us under SEC's rate-limit guidance."""
        elapsed = time.monotonic() - self._last_request_at
        remaining = MIN_REQUEST_INTERVAL_SECONDS - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def get_json(self, url: str) -> dict:
        """GET a URL and parse the response body as JSON."""
        self._throttle()
        response = self._http.get(url)
        response.raise_for_status()
        return response.json()

    def get_bytes(self, url: str) -> bytes:
        """GET a URL and return the raw response body (used for filing docs)."""
        self._throttle()
        response = self._http.get(url)
        response.raise_for_status()
        return response.content

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "EdgarClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
