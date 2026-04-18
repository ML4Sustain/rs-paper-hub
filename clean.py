#!/usr/bin/env python3
"""
Data cleaning pipeline for rs-paper-hub.

Usage:
    python clean.py                  # Clean output/papers.csv -> output/papers_cleaned.csv
    python clean.py --input x.csv    # Custom input
    python clean.py --inplace        # Overwrite original files
    python clean.py --dry-run        # Preview changes without saving
"""

import os
import json
import argparse
import logging

import pandas as pd

from cleaning.abstract_cleaner import clean_abstract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_cleaning(papers: list[dict]) -> tuple[list[dict], dict]:
    """
    Run all cleaning steps on paper records.

    Returns:
        (cleaned_papers, stats_dict)
    """
    stats = {
        "total": len(papers),
        "abstract_urls_extracted": 0,
        "code_filled": 0,
    }

    for paper in papers:
        old_code = paper.get("code", "")
        old_abstract = paper.get("Abstract", "")

        paper = clean_abstract(paper)

        # Track stats
        if paper.get("Abstract", "") != old_abstract:
            stats["abstract_urls_extracted"] += 1
        new_code = paper.get("code", "")
        if (not old_code or str(old_code) in ("nan", "")) and new_code and str(new_code) not in ("nan", ""):
            stats["code_filled"] += 1

    return papers, stats


def main():
    parser = argparse.ArgumentParser(description="Clean paper data")
    parser.add_argument(
        "--input", type=str, default="output/papers.csv",
        help="Input CSV file (default: output/papers.csv)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--inplace", action="store_true",
        help="Overwrite original files instead of creating *_cleaned versions"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without saving"
    )
    args = parser.parse_args()

    # Load
    logger.info(f"Loading {args.input}...")
    df = pd.read_csv(args.input).fillna("")
    papers = df.to_dict("records")
    logger.info(f"Loaded {len(papers)} papers")

    # Clean
    logger.info("Running cleaning pipeline...")
    papers, stats = run_cleaning(papers)

    # Report
    logger.info(f"Cleaning stats:")
    logger.info(f"  Total papers: {stats['total']}")
    logger.info(f"  Abstracts cleaned (URLs removed): {stats['abstract_urls_extracted']}")
    logger.info(f"  Code field filled from abstract: {stats['code_filled']}")

    if args.dry_run:
        logger.info("Dry run - no files saved")
        # Show a few examples
        for p in papers[:3]:
            if p.get("code") and str(p["code"]) != "nan":
                logger.info(f"  Example: {p['Title'][:60]}... -> code: {p['code']}")
        return

    # Save
    columns = [
        "Type", "Subtype", "Month", "Year", "Institute",
        "Title", "abbr.", "Paper_link", "Abstract",
        "code", "Publication", "BibTex", "Authors",
    ]

    if args.inplace:
        csv_path = args.input
        json_path = args.input.replace(".csv", ".json")
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        csv_path = os.path.join(args.output_dir, f"{base}_cleaned.csv")
        json_path = os.path.join(args.output_dir, f"{base}_cleaned.json")

    df_out = pd.DataFrame(papers, columns=columns).fillna("")
    df_out.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved to {csv_path}")

    clean_papers = [
        {k: ("" if pd.isna(v) else v) for k, v in p.items() if k in columns}
        for p in papers
    ]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clean_papers, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved to {json_path}")


if __name__ == "__main__":
    main()
