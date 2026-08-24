"""Phase 1 milestone script: for a handful of tickers, pull the last few
filings and cache the raw documents to data/filings/.

Run with: uv run python -m ingestion.edgar.ingest
"""

from ingestion.edgar.client import EdgarClient
from ingestion.edgar.download import cache_filing
from ingestion.edgar.filings import get_recent_filings
from ingestion.edgar.tickers import resolve_cik

# Vertical-slice tickers from the roadmap. Kept small deliberately — the goal
# is one ticker fully working before scaling out to five.
DEFAULT_TICKERS = ("NVDA", "AAPL", "MSFT")

FILINGS_PER_TICKER = 4


def ingest_ticker(client: EdgarClient, ticker: str) -> None:
    """Resolve one ticker's CIK, fetch its recent filings, and cache each one."""
    cik = resolve_cik(client, ticker)
    filings = get_recent_filings(client, ticker, cik, limit=FILINGS_PER_TICKER)

    print(f"{ticker} (CIK {cik}): {len(filings)} filings")
    for filing in filings:
        path = cache_filing(client, filing)
        print(f"  {filing.filing_date} {filing.form:<5} -> {path}")


def main() -> None:
    with EdgarClient() as client:
        for ticker in DEFAULT_TICKERS:
            ingest_ticker(client, ticker)


if __name__ == "__main__":
    main()
