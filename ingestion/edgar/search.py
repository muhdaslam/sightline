"""EDGAR full-text search: keyword search across filing contents.

This is a different tool than filings.py: the submissions API answers
"what has this company filed?", while full-text search answers "which
filings (from any company) mention this phrase?". We don't need it for the
initial "last 4 filings per ticker" ingestion, but it's useful later for
discovery (e.g. finding which filings discuss a specific risk factor).
"""

from urllib.parse import urlencode

from ingestion.edgar.client import EdgarClient

FULL_TEXT_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"


def full_text_search(
    client: EdgarClient,
    query: str,
    forms: tuple[str, ...] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Search EDGAR full-text search for `query`, optionally filtered by form type.

    Returns the raw list of hit dicts from SEC's response (each hit includes
    fields like accession number, form type, filer, and file date) — callers
    that need it turned into FilingMeta can map the fields themselves, since
    this endpoint's schema is looser/less stable than the submissions API.
    """
    params = {"q": query}
    if forms:
        params["forms"] = ",".join(forms)

    # EdgarClient.get_json only takes a full URL, so build the querystring
    # ourselves rather than adding query-param support just for this one caller.
    url = f"{FULL_TEXT_SEARCH_URL}?{urlencode(params)}"

    data = client.get_json(url)
    hits = data.get("hits", {}).get("hits", [])
    return hits[:limit]
