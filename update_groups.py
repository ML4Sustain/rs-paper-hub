#!/usr/bin/env python3
"""
Auto-update groups that have "auto": true in groups/index.json.

Matches papers by author name and writes Paper_link arrays to group JSON files.

Usage:
    python update_groups.py
    python update_groups.py --papers output/papers.json --groups-dir groups
"""

import os
import json
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def update_auto_groups(papers_path: str = "output/papers.json", groups_dir: str = "groups"):
    """Update all auto groups based on author matching."""
    index_path = os.path.join(groups_dir, "index.json")
    if not os.path.exists(index_path):
        logger.warning(f"Groups index not found: {index_path}")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        groups = json.load(f)

    auto_groups = [g for g in groups if g.get("auto")]
    if not auto_groups:
        logger.info("No auto groups found.")
        return

    logger.info(f"Found {len(auto_groups)} auto groups to update.")

    # Load papers
    with open(papers_path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    logger.info(f"Loaded {len(papers)} papers.")

    for group in auto_groups:
        authors = group.get("authors", [])
        if not authors:
            continue

        # Case-insensitive author matching
        authors_lower = [a.lower() for a in authors]

        matched = []
        for p in papers:
            paper_authors = str(p.get("Authors", "")).lower()
            if any(a in paper_authors for a in authors_lower):
                matched.append(p)

        # Sort by Date descending
        matched.sort(key=lambda p: p.get("Date", ""), reverse=True)

        # Extract links, deduplicate by base URL (keep highest version)
        import re
        base_map = {}  # base_url -> (version_num, full_link, date)
        for p in matched:
            link = p.get("Paper_link", "")
            if not link:
                continue
            m = re.search(r"v(\d+)$", link)
            ver = int(m.group(1)) if m else 0
            base = re.sub(r"v\d+$", "", link)
            if base not in base_map or ver > base_map[base][0]:
                base_map[base] = (ver, link, p.get("Date", ""))
        # Sort by date descending
        entries = sorted(base_map.values(), key=lambda x: x[2], reverse=True)
        links = [e[1] for e in entries]

        # Write group file
        group_path = os.path.join(groups_dir, group["file"])
        with open(group_path, "w", encoding="utf-8") as f:
            json.dump(links, f, ensure_ascii=False, indent=2)

        label = group.get("label", group["key"])
        logger.info(f"  {label}: {len(links)} papers -> {group_path}")


def main():
    parser = argparse.ArgumentParser(description="Auto-update groups by author matching")
    parser.add_argument("--papers", default="output/papers.json", help="Papers JSON file")
    parser.add_argument("--groups-dir", default="groups", help="Groups directory")
    args = parser.parse_args()

    update_auto_groups(args.papers, args.groups_dir)


if __name__ == "__main__":
    main()
