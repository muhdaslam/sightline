"""Download raw filing documents (PDF/HTML) and cache them to disk.

Caching matters here for two reasons: it avoids re-hitting SEC (and eating
into the rate-limit budget) on repeated runs, and it gives later pipeline
stages (page rendering, transcription) a stable local file to work from.
"""

from pathlib import Path

from ingestion.edgar.client import EdgarClient
from ingestion.edgar.filings import FilingMeta

# Raw filings live under data/ (gitignored, regenerable from EDGAR on demand).
RAW_FILINGS_DIR = Path("data/filings")


def _cache_path(filing: FilingMeta) -> Path:
    """Local path a filing's raw document is/would be cached at.

    One directory per ticker, one file per filing, named so the form type and
    date are visible without opening the file.
    """
    filename = f"{filing.filing_date}_{filing.form}_{filing.accession_number}_{filing.primary_document}"
    return RAW_FILINGS_DIR / filing.ticker / filename


def cache_filing(client: EdgarClient, filing: FilingMeta) -> Path:
    """Download `filing`'s primary document to disk, unless already cached.

    Returns the local path either way, so callers don't need to branch on
    whether a network request happened.
    """
    dest = _cache_path(filing)
    if dest.exists():
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    content = client.get_bytes(filing.document_url)
    dest.write_bytes(content)
    return dest
