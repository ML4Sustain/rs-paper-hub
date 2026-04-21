#!/usr/bin/env python3
"""
One-click pipeline: clean all data + filter VLM + classify.

Usage:
    python pipeline.py                # Process output/papers.json
    python pipeline.py --input x.json # Custom input
"""

import os
import json
import argparse
import logging
from collections import Counter

import pandas as pd

from cleaning.abstract_cleaner import clean_abstract
from cleaning.filter.vlm_filter import filter_vlm_papers
from cleaning.filter.agent_filter import filter_agent_papers
from cleaning.filter.uav_filter import filter_uav_papers
from cleaning.classifier import classify_papers
from cleaning.task_tagger import tag_all_papers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# All output columns
ALL_COLUMNS = [
    "Category", "Type", "Subtype", "Date", "Month", "Year", "Institute",
    "Title", "abbr.", "Paper_link", "Abstract",
    "code", "Publication", "BibTex", "Authors", "_tasks", "_added_date",
]

VLM_COLUMNS = ["Category"] + ALL_COLUMNS


def save(papers: list[dict], csv_path: str, json_path: str, columns: list[str]):
    """Save papers to CSV + JSON, NaN replaced with empty string."""
    df = pd.DataFrame(papers, columns=columns).fillna("")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    clean = [
        {k: ("" if pd.isna(v) else v) for k, v in p.items() if k in columns}
        for p in papers
    ]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)

    logger.info(f"  -> {csv_path} ({len(papers)} rows)")
    logger.info(f"  -> {json_path}")


def run(input_path: str, output_dir: str):
    # ── Load ──────────────────────────────────────────────
    logger.info(f"Loading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    logger.info(f"Loaded {len(papers)} papers")

    # ── Deduplicate by arxiv_id (strip version), keep latest version ──
    import re
    before = len(papers)
    seen = {}
    for p in papers:
        link = p.get("Paper_link", "")
        # Strip version suffix (e.g. v1, v2) to treat all versions as same paper
        key = re.sub(r'v\d+$', '', link) if link else str(id(p))
        existing = seen.get(key)
        if existing and existing.get("_added_date"):
            p["_added_date"] = existing["_added_date"]
        seen[key] = p
    papers = list(seen.values())
    if len(papers) < before:
        logger.info(f"  Deduplicated: {before} -> {len(papers)} ({before - len(papers)} duplicates removed)")

    # ── Stamp _added_date for new papers ─────────────────
    from datetime import date
    today_str = date.today().isoformat()

    def _has_added_date(p):
        v = p.get("_added_date")
        if not v:
            return False
        if isinstance(v, float) and pd.isna(v):
            return False
        if str(v).strip() in ("", "nan"):
            return False
        return True

    new_count = sum(1 for p in papers if not _has_added_date(p))
    for p in papers:
        if not _has_added_date(p):
            p["_added_date"] = today_str
    if new_count:
        logger.info(f"  Stamped _added_date={today_str} on {new_count} new papers")

    # ── Step 1: Clean abstracts → fill code field (incremental) ──
    need_code = [p for p in papers if not p.get("code") or str(p["code"]) in ("", "nan")]
    if need_code:
        logger.info(f"[1/11] Cleaning abstracts & extracting code URLs ({len(need_code)}/{len(papers)})...")
        code_filled = 0
        for p in need_code:
            clean_abstract(p)
            if p.get("code") and str(p["code"]) not in ("", "nan"):
                code_filled += 1
        logger.info(f"  Code field filled from abstract: {code_filled}")
    else:
        logger.info("[1/11] Code extraction: all papers already have code field, skipped")

    # ── Step 2: Classify (incremental) ────────────────────
    need_classify = [p for p in papers if not p.get("Category")]
    if need_classify:
        logger.info(f"[2/11] Classifying papers ({len(need_classify)}/{len(papers)})...")
        classify_papers(need_classify)
    else:
        logger.info("[2/11] Classification: all papers already classified, skipped")

    # ── Step 3: Tag tasks (incremental) ───────────────────
    need_tasks = [p for p in papers if "_tasks" not in p]
    if need_tasks:
        logger.info(f"[3/11] Tagging tasks ({len(need_tasks)}/{len(papers)})...")
        tag_all_papers(need_tasks)
    else:
        logger.info("[3/11] Task tagging: all papers already tagged, skipped")

    all_cat_counter = Counter(p.get("Category", "Other") for p in papers)
    for cat, count in all_cat_counter.most_common():
        logger.info(f"  {cat}: {count}")

    # ── Step 3: Save cleaned full dataset ─────────────────
    logger.info("[4/11] Saving cleaned dataset...")
    save(
        papers,
        os.path.join(output_dir, "papers.csv"),
        os.path.join(output_dir, "papers.json"),
        ALL_COLUMNS,
    )

    # ── Step 4: Filter VLM papers ─────────────────────────
    logger.info("[5/11] Filtering VLM-related papers...")
    matched, annotated = filter_vlm_papers(papers)
    logger.info(f"  VLM-related: {len(matched)} / {len(papers)}")

    # ── Step 5: Classify VLM papers ───────────────────────
    logger.info("[6/11] Classifying VLM papers...")
    classify_papers(matched)


    cat_counter = Counter(p.get("Category", "Other") for p in matched)
    for cat, count in cat_counter.most_common():
        logger.info(f"  {cat}: {count}")

    year_counter = Counter(p.get("Year", "?") for p in matched)
    logger.info("  Year distribution:")
    for year in sorted(year_counter):
        logger.info(f"    {year}: {year_counter[year]}")

    # ── Save VLM outputs ──────────────────────────────────
    logger.info("Saving VLM outputs...")
    save(
        matched,
        os.path.join(output_dir, "papers_vlm.csv"),
        os.path.join(output_dir, "papers_vlm.json"),
        VLM_COLUMNS,
    )

    # Annotated full list
    annotated_path = os.path.join(output_dir, "papers_vlm_annotated.json")
    with open(annotated_path, "w", encoding="utf-8") as f:
        json.dump(annotated, f, ensure_ascii=False, indent=2)
    logger.info(f"  -> {annotated_path}")

    # ── Step 7: Filter Agent papers ──────────────────────
    logger.info("[7/11] Filtering Agent-related papers...")
    agent_matched, agent_annotated = filter_agent_papers(papers)
    logger.info(f"  Agent-related: {len(agent_matched)} / {len(papers)}")

    # ── Step 8: Classify Agent papers ────────────────────
    logger.info("[8/11] Classifying Agent papers...")
    classify_papers(agent_matched)

    agent_cat_counter = Counter(p.get("Category", "Other") for p in agent_matched)
    for cat, count in agent_cat_counter.most_common():
        logger.info(f"  {cat}: {count}")

    # ── Save Agent outputs ────────────────────────────────
    logger.info("Saving Agent outputs...")
    save(
        agent_matched,
        os.path.join(output_dir, "papers_agent.csv"),
        os.path.join(output_dir, "papers_agent.json"),
        ALL_COLUMNS,
    )

    agent_annotated_path = os.path.join(output_dir, "papers_agent_annotated.json")
    with open(agent_annotated_path, "w", encoding="utf-8") as f:
        json.dump(agent_annotated, f, ensure_ascii=False, indent=2)
    logger.info(f"  -> {agent_annotated_path}")

    # ── Step 9: Filter UAV papers ────────────────────────
    logger.info("[9/11] Filtering UAV-related papers...")
    uav_matched, uav_annotated = filter_uav_papers(papers)
    logger.info(f"  UAV-related: {len(uav_matched)} / {len(papers)}")

    # ── Step 10: Classify UAV papers ─────────────────────
    logger.info("[10/11] Classifying UAV papers...")
    classify_papers(uav_matched)

    uav_cat_counter = Counter(p.get("Category", "Other") for p in uav_matched)
    for cat, count in uav_cat_counter.most_common():
        logger.info(f"  {cat}: {count}")

    # ── Save UAV outputs ─────────────────────────────────
    logger.info("Saving UAV outputs...")
    save(
        uav_matched,
        os.path.join(output_dir, "papers_uav.csv"),
        os.path.join(output_dir, "papers_uav.json"),
        ALL_COLUMNS,
    )

    uav_annotated_path = os.path.join(output_dir, "papers_uav_annotated.json")
    with open(uav_annotated_path, "w", encoding="utf-8") as f:
        json.dump(uav_annotated, f, ensure_ascii=False, indent=2)
    logger.info(f"  -> {uav_annotated_path}")

    # ── Step 11: Update auto groups ────────────────────
    logger.info("[11/12] Updating auto groups...")
    from update_groups import update_auto_groups
    update_auto_groups(os.path.join(output_dir, "papers.json"), "groups")

    # ── Step 12: Generate Atom feeds for Zotero ──────────
    logger.info("[12/12] Generating Atom feeds...")
    from rss_generator import generate_feeds
    generate_feeds(papers, matched, agent_matched, uav_matched, output_dir,
                   site_url="https://rspaper.top")

    # ── Summary ───────────────────────────────────────────
    logger.info("=" * 50)
    logger.info(f"Done! Total: {len(papers)} | VLM: {len(matched)} | Agent: {len(agent_matched)} | UAV: {len(uav_matched)}")
    logger.info(f"  papers.csv/json             - all {len(papers)} papers (cleaned)")
    logger.info(f"  papers_vlm.csv/json         - {len(matched)} VLM papers (with Category)")
    logger.info(f"  papers_vlm_annotated.json   - full list with VLM flags")
    logger.info(f"  papers_agent.csv/json       - {len(agent_matched)} Agent papers (with Category)")
    logger.info(f"  papers_agent_annotated.json - full list with Agent flags")
    logger.info(f"  papers_uav.csv/json         - {len(uav_matched)} UAV papers (with Category)")
    logger.info(f"  papers_uav_annotated.json   - full list with UAV flags")


def main():
    parser = argparse.ArgumentParser(description="One-click: clean + filter + classify")
    parser.add_argument(
        "--input", type=str, default="output/papers.json",
        help="Input JSON file (default: output/papers.json)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="output",
        help="Output directory (default: output)"
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    run(args.input, args.output_dir)


if __name__ == "__main__":
    main()
