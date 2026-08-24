"""Resolve stock tickers (e.g. "NVDA") to SEC CIK numbers.

EDGAR's per-company APIs are keyed by CIK (Central Index Key), not ticker, so
every filing lookup starts here. SEC publishes a single JSON file mapping
every ticker to its CIK; we cache that file to disk so repeated runs don't
re-download it.
"""

import json
from pathlib import Path

from ingestion.edgar.client import EdgarClient

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Cached under data/ (gitignored, regenerable) so we don't hit SEC on every run.
CACHE_PATH = Path("data/edgar/company_tickers.json")


def _load_ticker_map(client: EdgarClient) -> dict:
    """Return the raw {index: {cik_str, ticker, title}} mapping, using the
    on-disk cache if present, else fetching and caching it."""
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())

    data = client.get_json(COMPANY_TICKERS_URL)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(data))
    return data


def resolve_cik(client: EdgarClient, ticker: str) -> str:
    """Return the 10-digit, zero-padded CIK for a ticker (as EDGAR URLs expect).

    Raises ValueError if the ticker isn't found in SEC's mapping.
    """
    ticker = ticker.upper()
    ticker_map = _load_ticker_map(client)

    for entry in ticker_map.values():
        if entry["ticker"] == ticker:
            return f"{entry['cik_str']:010d}"

    raise ValueError(f"Ticker {ticker!r} not found in SEC company_tickers.json")
