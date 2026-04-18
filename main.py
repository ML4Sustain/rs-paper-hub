#!/usr/bin/env python3
"""
arXiv Remote Sensing Paper Scraper

Fetches remote sensing papers from arXiv (2022-present),
enriches with code links from Papers With Code,
and exports to CSV + JSON. Supports resumable operation.
"""

import os
import json
import argparse
import logging

import pandas as pd

from config import OUTPUT_DIR, CSV_FILENAME, JSON_FILENAME, START_YEAR, END_YEAR
from scraper import fetch_papers
from parser import parse_results
from pwc_client import PapersWithCodeClient
from downloader import download_papers
from progress import ProgressTracker


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def save_results(papers: list[dict], output_dir: str):
    """Save papers to CSV and JSON."""
    os.makedirs(output_dir, exist_ok=True)

    columns = [
        "Type", "Subtype", "Month", "Year", "Institute",
        "Title", "abbr.", "Paper_link", "Abstract",
        "code", "Publication", "BibTex", "Authors",
    ]

    # CSV
    df = pd.DataFrame(papers, columns=columns)
    csv_path = os.path.join(output_dir, CSV_FILENAME)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logging.info(f"Saved {len(papers)} papers to {csv_path}")

    # JSON
    json_path = os.path.join(output_dir, JSON_FILENAME)
    clean_papers = [{k: v for k, v in p.items() if k in columns} for p in papers]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clean_papers, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved {len(papers)} papers to {json_path}")


def load_existing(output_dir: str) -> set[str]:
    """Load existing paper links to support incremental scraping."""
    csv_path = os.path.join(output_dir, CSV_FILENAME)
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return set(df["Paper_link"].dropna())
        except Exception:
            pass
    return set()


def main():
    parser = argparse.ArgumentParser(
        description="Scrape arXiv remote sensing papers"
    )
    parser.add_argument(
        "--start-year", type=int, default=START_YEAR,
        help=f"Start year (default: {START_YEAR})"
    )
    parser.add_argument(
        "--end-year", type=int, default=END_YEAR,
        help=f"End year (default: {END_YEAR})"
    )
    parser.add_argument(
        "--max-results", type=int, default=None,
        help="Max papers to fetch (default: all)"
    )
    parser.add_argument(
        "--output-dir", type=str, default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--with-code", action="store_true",
        help="Enable Papers With Code lookup for code repos (off by default)"
    )
    parser.add_argument(
        "--download", action="store_true",
        help="Download paper PDFs to local storage"
    )
    parser.add_argument(
        "--download-only", action="store_true",
        help="Only download PDFs for papers already in output CSV (skip scraping)"
    )
    parser.add_argument(
        "--incremental", action="store_true",
        help="Skip papers already in output CSV"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current progress and exit"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose logging"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    os.makedirs(args.output_dir, exist_ok=True)
    progress = ProgressTracker(args.output_dir)

    # Status mode
    if args.status:
        print(progress.summary())
        return

    # Download-only mode
    if args.download_only:
        csv_path = os.path.join(args.output_dir, CSV_FILENAME)
        if not os.path.exists(csv_path):
            logger.error(f"No existing data found at {csv_path}. Run scraper first.")
            return
        df = pd.read_csv(csv_path)
        papers = df.to_dict("records")
        logger.info(f"Loaded {len(papers)} papers from {csv_path}")
        download_papers(papers, args.output_dir, progress=progress)
        logger.info("Done!")
        return

    # Step 1: Fetch from arXiv (resumable by month)
    if progress.scrape_completed and not args.max_results:
        logger.info(
            f"Scraping already completed ({progress.total_scraped} papers). "
            "Use --incremental to add new papers, or delete progress.json to restart."
        )
    else:
        logger.info(
            f"Fetching papers from arXiv ({args.start_year}-{args.end_year})..."
        )
        if progress.last_scraped_year:
            logger.info(
                f"Resuming from {progress.last_scraped_year}-{progress.last_scraped_month:02d} "
                f"({progress.total_scraped} papers already scraped)"
            )

    results = fetch_papers(
        start_year=args.start_year,
        end_year=args.end_year,
        max_results=args.max_results,
        progress=progress,
    )
    logger.info(f"Fetched {len(results)} papers from arXiv")

    if not results:
        logger.warning("No papers found. Check your search query.")
        return

    # Step 2: Parse results
    logger.info("Parsing paper metadata...")
    papers = parse_results(results)

    # Step 3: Incremental mode - filter out existing
    if args.incremental:
        existing = load_existing(args.output_dir)
        before = len(papers)
        papers = [p for p in papers if p["Paper_link"] not in existing]
        logger.info(f"Incremental: {before - len(papers)} existing skipped, {len(papers)} new")

    if not papers:
        logger.info("No new papers to process.")
        return

    # Step 4: Enrich with code links (opt-in)
    if args.with_code:
        from tqdm import tqdm
        logger.info("Querying Papers With Code for code repos...")
        pwc = PapersWithCodeClient()
        pbar = tqdm(total=len(papers), desc="Fetching code links")
        pwc.enrich_papers(papers, progress_callback=lambda i, t: pbar.update(1))
        pbar.close()

        code_count = sum(1 for p in papers if p.get("code"))
        logger.info(f"Found code repos for {code_count}/{len(papers)} papers")

    # Step 5: Save results
    if args.incremental:
        csv_path = os.path.join(args.output_dir, CSV_FILENAME)
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            new_df = pd.DataFrame(papers)
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            papers = combined.to_dict("records")

    save_results(papers, args.output_dir)

    # Step 6: Download PDFs if requested (resumable)
    if args.download:
        download_papers(papers, args.output_dir, progress=progress)

    logger.info("Done!")
    logger.info(f"Progress: {progress.summary()}")


if __name__ == "__main__":
    main()
