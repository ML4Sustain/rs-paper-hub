"""arXiv API scraper for remote sensing papers."""

import time
import logging
from datetime import datetime

import arxiv
from tqdm import tqdm

from config import (
    SEARCH_QUERY,
    START_YEAR,
    END_YEAR,
    BATCH_SIZE,
    REQUEST_DELAY,
    MAX_RETRIES,
)
from progress import ProgressTracker

logger = logging.getLogger(__name__)


def build_query(year: int, month: int | None = None) -> str:
    """Build arXiv search query for a specific year/month."""
    base = SEARCH_QUERY
    if month:
        # submittedDate format: YYYYMMDDHHNN
        start = f"{year}{month:02d}01"
        if month == 12:
            end = f"{year + 1}0101"
        else:
            end = f"{year}{month + 1:02d}01"
        date_filter = f" AND submittedDate:[{start}0000 TO {end}0000]"
        return f'({base}){date_filter}'
    return base


def _build_month_list(start_year: int, end_year: int) -> list[tuple[int, int]]:
    """Build list of (year, month) tuples to scrape."""
    current_year = datetime.now().year
    current_month = datetime.now().month
    months = []
    for year in range(start_year, min(end_year, current_year) + 1):
        max_month = 12
        if year == current_year:
            max_month = current_month
        for month in range(1, max_month + 1):
            months.append((year, month))
    return months


def _build_date_range_query(date_from: datetime, date_to: datetime) -> str:
    """Build arXiv search query for a specific date range."""
    start = date_from.strftime("%Y%m%d")
    end = date_to.strftime("%Y%m%d")
    return f'({SEARCH_QUERY}) AND submittedDate:[{start}0000 TO {end}2359]'


def fetch_papers(
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
    max_results: int | None = None,
    progress: ProgressTracker | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[arxiv.Result]:
    """
    Fetch papers from arXiv API.

    If date_from/date_to are provided, fetches that exact date range in one query.
    Otherwise, iterates month by month over the year range.

    Returns:
        List of arxiv.Result objects
    """
    all_results = []
    total_fetched = 0

    client = arxiv.Client(
        page_size=BATCH_SIZE,
        delay_seconds=REQUEST_DELAY,
        num_retries=MAX_RETRIES,
    )

    # Date-range mode (for --update): single query for the date range
    if date_from and date_to:
        query = _build_date_range_query(date_from, date_to)
        logger.info(f"Querying date range: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}")

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        retry_count = 0
        while True:
            try:
                for result in client.results(search):
                    all_results.append(result)
                    total_fetched += 1
                    if max_results and total_fetched >= max_results:
                        break
                break
            except arxiv.UnexpectedEmptyPageError:
                break
            except Exception as e:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    logger.error(f"Failed after {MAX_RETRIES} retries: {e}")
                    break
                wait = REQUEST_DELAY * (2 ** retry_count)
                logger.warning(f"Retry {retry_count}, waiting {wait}s...")
                time.sleep(wait)

        if progress:
            progress.mark_scrape_done(total_fetched)

        logger.info(f"Total fetched: {total_fetched} papers")
        return all_results

    # Month-by-month mode (for full scrape)
    months = _build_month_list(start_year, end_year)

    pbar = tqdm(
        months,
        desc="Scraping arXiv",
        unit="month",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} months [{elapsed}<{remaining}] {postfix}",
    )

    for year, month in pbar:
        if max_results and total_fetched >= max_results:
            break

        # Skip already-scraped months
        if progress and progress.should_skip_month(year, month):
            pbar.set_postfix_str(f"{year}-{month:02d} skipped")
            continue

        pbar.set_postfix_str(f"{year}-{month:02d} fetching...")

        query = build_query(year, month)
        search = arxiv.Search(
            query=query,
            max_results=max_results - total_fetched if max_results else None,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Ascending,
        )

        month_count = 0
        retry_count = 0
        while True:
            try:
                for result in client.results(search):
                    all_results.append(result)
                    total_fetched += 1
                    month_count += 1

                    if max_results and total_fetched >= max_results:
                        break
                break  # success
            except arxiv.UnexpectedEmptyPageError:
                break
            except Exception as e:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    logger.error(f"Failed after {MAX_RETRIES} retries for {year}-{month:02d}: {e}")
                    break
                wait = REQUEST_DELAY * (2 ** retry_count)
                pbar.set_postfix_str(f"{year}-{month:02d} retry {retry_count}...")
                time.sleep(wait)

        pbar.set_postfix_str(f"{year}-{month:02d}: {month_count} papers (total: {total_fetched})")

        # Save progress after each month
        if progress:
            progress.update_scrape(year, month, total_fetched)

    pbar.close()

    if progress:
        progress.mark_scrape_done(total_fetched)

    logger.info(f"Total fetched: {total_fetched} papers")
    return all_results
