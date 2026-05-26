#!/usr/bin/env python3
"""
Backfill geospatial papers from arXiv (2020–present).

Fetches papers matching 'geospatial' that were missed by the original
'remote sensing' / 'earth observation' search query, and merges them
into the existing papers.csv/json (incremental, no duplicates).

Run once after updating config.py to include geospatial in SEARCH_QUERY:
    python backfill_geospatial.py
Then run the pipeline:
    python pipeline.py
"""

import json
import logging
import os
import re
import time
from datetime import datetime

import arxiv
import pandas as pd
from tqdm import tqdm

from config import (
    BATCH_SIZE,
    CSV_FILENAME,
    END_YEAR,
    JSON_FILENAME,
    MAX_RETRIES,
    OUTPUT_DIR,
    REQUEST_DELAY,
    START_YEAR,
)
from parser import parse_results

GEOSPATIAL_QUERY = 'ti:"geospatial" OR abs:"geospatial"'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _strip_version(link: str) -> str:
    return re.sub(r"v\d+$", "", link) if link else link


def load_existing_ids(output_dir: str) -> set[str]:
    csv_path = os.path.join(output_dir, CSV_FILENAME)
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return set(_strip_version(str(link)) for link in df["Paper_link"].dropna())
        except Exception:
            pass
    return set()


def fetch_geospatial_papers(start_year: int, end_year: int) -> list:
    """Fetch papers matching the geospatial query, month by month."""
    client = arxiv.Client(
        page_size=BATCH_SIZE,
        delay_seconds=REQUEST_DELAY,
        num_retries=MAX_RETRIES,
    )

    current_year = datetime.now().year
    current_month = datetime.now().month

    months = []
    for year in range(start_year, min(end_year, current_year) + 1):
        max_month = 12 if year < current_year else current_month
        for month in range(1, max_month + 1):
            months.append((year, month))

    all_results = []
    pbar = tqdm(months, desc="Fetching geospatial papers", unit="month")

    for year, month in pbar:
        start = f"{year}{month:02d}01"
        end = f"{year + 1}0101" if month == 12 else f"{year}{month + 1:02d}01"
        query = f"({GEOSPATIAL_QUERY}) AND submittedDate:[{start}0000 TO {end}0000]"

        search = arxiv.Search(
            query=query,
            max_results=None,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Ascending,
        )

        month_count = 0
        retry_count = 0
        while True:
            try:
                for result in client.results(search):
                    all_results.append(result)
                    month_count += 1
                break
            except arxiv.UnexpectedEmptyPageError:
                break
            except Exception as e:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    logger.error(f"Failed after {MAX_RETRIES} retries for {year}-{month:02d}: {e}")
                    break
                wait = REQUEST_DELAY * (2**retry_count)
                logger.warning(f"{year}-{month:02d} retry {retry_count}, waiting {wait}s...")
                time.sleep(wait)

        pbar.set_postfix_str(f"{year}-{month:02d}: {month_count} found (total: {len(all_results)})")

    pbar.close()
    return all_results


def main():
    logger.info("Starting geospatial paper backfill...")
    logger.info(f"Query: {GEOSPATIAL_QUERY}")
    logger.info(f"Date range: {START_YEAR}–{END_YEAR}")

    existing_ids = load_existing_ids(OUTPUT_DIR)
    logger.info(f"Existing papers in DB: {len(existing_ids)}")

    results = fetch_geospatial_papers(START_YEAR, END_YEAR)
    logger.info(f"Fetched {len(results)} geospatial papers from arXiv")

    if not results:
        logger.warning("No geospatial papers found.")
        return

    papers = parse_results(results)

    new_papers = [p for p in papers if _strip_version(p.get("Paper_link", "")) not in existing_ids]
    logger.info(f"New papers (not in existing DB): {len(new_papers)}")

    if not new_papers:
        logger.info("No new papers to add. DB is already up to date.")
        return

    csv_path = os.path.join(OUTPUT_DIR, CSV_FILENAME)
    json_path = os.path.join(OUTPUT_DIR, JSON_FILENAME)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        combined = pd.concat([existing_df, pd.DataFrame(new_papers)], ignore_index=True)
    else:
        combined = pd.DataFrame(new_papers)

    combined.to_csv(csv_path, index=False, encoding="utf-8-sig")

    columns = [
        "Type", "Subtype", "Date", "Month", "Year", "Institute",
        "Title", "abbr.", "Paper_link", "Abstract",
        "code", "Publication", "BibTex", "Authors", "_added_date",
    ]
    all_papers = combined.to_dict("records")
    clean_papers = [{k: v for k, v in p.items() if k in columns} for p in all_papers]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clean_papers, f, ensure_ascii=False, indent=2)

    logger.info(f"Added {len(new_papers)} new geospatial papers → {csv_path}")
    logger.info("Done! Run `python pipeline.py` to classify and filter the new papers.")


if __name__ == "__main__":
    main()
