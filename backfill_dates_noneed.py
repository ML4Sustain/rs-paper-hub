#!/usr/bin/env python3
"""
Backfill exact dates for existing papers by querying arXiv API.

Usage:
    python backfill_dates.py                        # Default: output/papers.json
    python backfill_dates.py --input output/x.json  # Custom input
"""

import json
import time
import argparse
import logging

import arxiv
from tqdm import tqdm

from config import REQUEST_DELAY, MAX_RETRIES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # query up to 50 IDs per request


def extract_arxiv_id(paper_link: str) -> str:
    """Extract arXiv ID from paper link."""
    return paper_link.split("/abs/")[-1]


def backfill_dates(papers: list[dict]) -> int:
    """
    Query arXiv API to fill in exact Date for papers missing it.

    Args:
        papers: List of paper dicts (modified in place)

    Returns:
        Number of papers updated
    """
    # Find papers needing date
    need_date = []
    for p in papers:
        if not p.get("Date") or str(p["Date"]) in ("", "nan"):
            link = p.get("Paper_link", "")
            if link:
                need_date.append(p)

    if not need_date:
        logger.info("All papers already have dates")
        return 0

    logger.info(f"{len(need_date)} papers need date backfill")

    client = arxiv.Client(
        page_size=BATCH_SIZE,
        delay_seconds=REQUEST_DELAY,
        num_retries=MAX_RETRIES,
    )

    updated = 0
    # Process in batches
    for i in tqdm(range(0, len(need_date), BATCH_SIZE), desc="Backfilling dates", unit="batch"):
        batch = need_date[i:i + BATCH_SIZE]
        id_list = [extract_arxiv_id(p["Paper_link"]) for p in batch]

        # Build a lookup by arXiv ID
        id_to_paper = {}
        for p in batch:
            aid = extract_arxiv_id(p["Paper_link"])
            # Normalize: strip version for matching
            id_to_paper[aid] = p
            base = aid.split("v")[0] if "v" in aid else aid
            id_to_paper[base] = p

        try:
            search = arxiv.Search(id_list=id_list)
            for result in client.results(search):
                rid = result.entry_id.split("/abs/")[-1]
                base_rid = rid.split("v")[0] if "v" in rid else rid

                paper = id_to_paper.get(rid) or id_to_paper.get(base_rid)
                if paper:
                    paper["Date"] = result.published.strftime("%Y-%m-%d")
                    paper["Month"] = result.published.month
                    paper["Year"] = result.published.year
                    updated += 1

        except Exception as e:
            logger.warning(f"Batch query failed: {e}")

        time.sleep(REQUEST_DELAY)

    return updated


def main():
    parser = argparse.ArgumentParser(description="Backfill exact dates for papers")
    parser.add_argument(
        "--input", type=str, default="output/papers.json",
        help="Input JSON file"
    )
    args = parser.parse_args()

    # Load
    logger.info(f"Loading {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        papers = json.load(f)
    logger.info(f"Loaded {len(papers)} papers")

    has_date = sum(1 for p in papers if p.get("Date") and str(p["Date"]) not in ("", "nan"))
    logger.info(f"Already have date: {has_date}, missing: {len(papers) - has_date}")

    # Backfill
    updated = backfill_dates(papers)
    logger.info(f"Updated {updated} papers with exact dates")

    # Save back
    with open(args.input, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved to {args.input}")

    # Also update CSV
    csv_path = args.input.replace(".json", ".csv")
    import pandas as pd
    df = pd.DataFrame(papers).fillna("")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved to {csv_path}")


if __name__ == "__main__":
    main()
