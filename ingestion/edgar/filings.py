"""Fetch a company's filing history from EDGAR's submissions API and pick the
filings we actually want to ingest.

data.sec.gov/submissions/CIK##########.json returns (among other things) a
"recent" block of parallel arrays — one entry per filing, indexed by
position — rather than a list of filing objects. We zip those arrays into a
list of `FilingMeta` records, which is much easier for the rest of the
pipeline to work with.
"""

from dataclasses import dataclass

from ingestion.edgar.client import EdgarClient

SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/CIK{cik}.json"

# Filing types that actually matter for equity research. Without this filter,
# "recent filings" for an active company is dominated by ownership forms
# (Form 3/4/5) rather than the 10-Ks/10-Qs/8-Ks we care about.
DEFAULT_FORMS = ("10-K", "10-Q", "8-K")


@dataclass(frozen=True)
class FilingMeta:
    """Everything we need to locate and cache one filing document."""

    ticker: str
    cik: str
    accession_number: str  # e.g. "0000320193-23-000106"
    form: str  # e.g. "10-K"
    filing_date: str  # "YYYY-MM-DD"
    primary_document: str  # filename of the main document, e.g. "aapl-20230930.htm"

    @property
    def document_url(self) -> str:
        """Direct URL to the primary filing document on EDGAR's archive host."""
        accession_no_dashes = self.accession_number.replace("-", "")
        cik_no_leading_zeros = str(int(self.cik))
        return (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_no_leading_zeros}/{accession_no_dashes}/{self.primary_document}"
        )


def get_recent_filings(
    client: EdgarClient,
    ticker: str,
    cik: str,
    forms: tuple[str, ...] = DEFAULT_FORMS,
    limit: int = 4,
) -> list[FilingMeta]:
    """Return the `limit` most recent filings for `cik` whose form is in `forms`.

    The submissions API already returns filings newest-first, so filtering
    preserves that order and we just take the first `limit` matches.
    """
    url = SUBMISSIONS_URL_TEMPLATE.format(cik=cik)
    submissions = client.get_json(url)
    recent = submissions["filings"]["recent"]

    # "recent" is a set of parallel arrays (one value per filing, same index
    # across arrays) rather than a list of per-filing dicts — zip them up.
    filings = zip(
        recent["accessionNumber"],
        recent["form"],
        recent["filingDate"],
        recent["primaryDocument"],
    )

    matches: list[FilingMeta] = []
    for accession_number, form, filing_date, primary_document in filings:
        if form not in forms:
            continue
        matches.append(
            FilingMeta(
                ticker=ticker,
                cik=cik,
                accession_number=accession_number,
                form=form,
                filing_date=filing_date,
                primary_document=primary_document,
            )
        )
        if len(matches) == limit:
            break

    return matches
