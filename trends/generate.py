#!/usr/bin/env python3
"""
Generate trend statistics from papers data (incremental).

First run: full computation from all papers.
Subsequent runs: only process papers with _added_date > last update,
merge incremental counts into existing trends.json.

Use --full to force a full recomputation.
"""

import json
import os
import argparse
from collections import Counter, defaultdict
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = SCRIPT_DIR
TRENDS_PATH = os.path.join(OUTPUT_DIR, "trends.json")

DATA_FILES = {
    "all": "papers.json",
    "vlm": "papers_vlm.json",
    "uav": "papers_uav.json",
    "agent": "papers_agent.json",
}


def load_papers(filename):
    path = os.path.join(ROOT_DIR, "output", filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_existing():
    """Load existing trends.json, return (data, last_updated) or (None, None)."""
    if not os.path.exists(TRENDS_PATH):
        return None, None
    with open(TRENDS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    last_updated = data.get("_last_updated")
    return data, last_updated


def compute_trends(papers):
    """Compute full statistics from a list of papers."""
    yearly = Counter()
    monthly = defaultdict(Counter)
    author_counter = Counter()
    author_monthly = defaultdict(lambda: defaultdict(Counter))
    author_yearly = defaultdict(Counter)

    for p in papers:
        year = p.get("Year")
        month = p.get("Month")
        authors_str = p.get("Authors", "")

        if year:
            yearly[year] += 1
        if year and month:
            monthly[year][month] += 1

        if authors_str:
            for a in authors_str.split(","):
                name = a.strip()
                if name:
                    author_counter[name] += 1
                    if year:
                        author_yearly[name][year] += 1
                    if year and month:
                        author_monthly[name][year][month] += 1

    return _format_result(yearly, monthly, author_counter,
                          author_yearly, author_monthly, len(papers))


def _format_result(yearly, monthly, author_counter,
                   author_yearly, author_monthly, total):
    yearly_sorted = sorted(yearly.items(), key=lambda x: x[0])

    monthly_sorted = {}
    for year in sorted(monthly.keys()):
        monthly_sorted[str(year)] = {
            str(m): monthly[year].get(m, 0) for m in range(1, 13)
        }

    top_authors = author_counter.most_common(100)
    top_author_details = []
    for name, count in top_authors:
        ay = author_yearly[name]
        am = author_monthly[name]
        yearly_dist = {str(y): c for y, c in sorted(ay.items())}
        monthly_dist = {}
        for y in sorted(am.keys()):
            monthly_dist[str(y)] = {str(m): am[y].get(m, 0) for m in range(1, 13)}
        top_author_details.append({
            "name": name, "count": count,
            "yearly": yearly_dist, "monthly": monthly_dist,
        })

    return {
        "yearly": {str(y): c for y, c in yearly_sorted},
        "monthly": monthly_sorted,
        "top_authors": top_author_details,
        "total": total,
    }


def merge_into(existing, delta):
    """Merge incremental delta into existing dataset stats in-place."""
    # --- yearly ---
    for y, c in delta["yearly"].items():
        existing["yearly"][y] = existing["yearly"].get(y, 0) + c
    # re-sort by year key
    existing["yearly"] = dict(sorted(existing["yearly"].items()))

    # --- monthly ---
    for y, months in delta["monthly"].items():
        if y not in existing["monthly"]:
            existing["monthly"][y] = {str(m): 0 for m in range(1, 13)}
        for m, c in months.items():
            existing["monthly"][y][m] = existing["monthly"][y].get(m, 0) + c

    # --- total ---
    existing["total"] = existing.get("total", 0) + delta["total"]

    # --- top_authors: merge counts, then re-rank top 100 ---
    author_map = {}
    for a in existing.get("top_authors", []):
        author_map[a["name"]] = a

    for a in delta["top_authors"]:
        name = a["name"]
        if name in author_map:
            e = author_map[name]
            e["count"] += a["count"]
            # merge yearly
            for y, c in a.get("yearly", {}).items():
                e["yearly"][y] = e["yearly"].get(y, 0) + c
            # merge monthly
            for y, months in a.get("monthly", {}).items():
                if y not in e["monthly"]:
                    e["monthly"][y] = {str(m): 0 for m in range(1, 13)}
                for m, c in months.items():
                    e["monthly"][y][m] = e["monthly"][y].get(m, 0) + c
        else:
            author_map[name] = {
                "name": name, "count": a["count"],
                "yearly": dict(a.get("yearly", {})),
                "monthly": {y: dict(ms) for y, ms in a.get("monthly", {}).items()},
            }

    # Re-sort top 100
    all_authors = sorted(author_map.values(), key=lambda x: -x["count"])
    existing["top_authors"] = all_authors[:100]


def main():
    parser = argparse.ArgumentParser(description="Generate trends (incremental)")
    parser.add_argument("--full", action="store_true",
                        help="Force full recomputation ignoring existing data")
    args = parser.parse_args()

    existing_data, last_updated = load_existing()
    is_incremental = (not args.full) and existing_data and last_updated
    today_str = date.today().isoformat()

    if is_incremental:
        print(f"Incremental update (papers added after {last_updated})...")
    else:
        print("Full computation...")
        existing_data = {}

    result = dict(existing_data)
    any_new = False

    for key, filename in DATA_FILES.items():
        papers = load_papers(filename)
        if not papers:
            continue

        if is_incremental and key in result and key != "_last_updated":
            # Filter to only new papers
            new_papers = [p for p in papers
                          if (p.get("_added_date") or "") > last_updated]
            if not new_papers:
                print(f"  [{key}] No new papers, skipped")
                continue
            print(f"  [{key}] {len(new_papers)} new papers (of {len(papers)} total)")
            delta = compute_trends(new_papers)
            merge_into(result[key], delta)
            any_new = True
        else:
            print(f"  [{key}] Full: {len(papers)} papers")
            result[key] = compute_trends(papers)
            any_new = True

    if not any_new and is_incremental:
        print("No new papers across all datasets, trends.json unchanged.")
        return

    result["_last_updated"] = today_str

    with open(TRENDS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Trends written to {TRENDS_PATH} (updated: {today_str})")


if __name__ == "__main__":
    main()
