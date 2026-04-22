#!/usr/bin/env python3
"""
Pre-compute weekly hot paper rankings for the Radar page.

Mirrors the JS scoring logic in index.html (getEffectiveKeywords + scorePaper)
and outputs a lightweight output/radar_weekly.json consumed directly by the
frontend — replacing the expensive full-JSON fetch + in-browser compute.

Run standalone:
    python generate_radar_weekly.py

Or via pipeline.py (added as the final step automatically).
"""

import json
from datetime import date, timedelta, timezone, datetime
from pathlib import Path

ROOT          = Path(__file__).parent
OUTPUT_DIR    = ROOT / "output"
WORDCLOUD_DIR = ROOT / "wordcloud"

SOURCES = {
    "all":   "papers.json",
    "vlm":   "papers_vlm.json",
    "uav":   "papers_uav.json",
    "agent": "papers_agent.json",
    "sar":   "papers_sar.json",
    "hyp":   "papers_hyp.json",
}

# Must match JS yearWeights in getEffectiveKeywords
YEAR_WEIGHTS    = {"2025": 2.5, "2024": 2.0, "2023": 1.2, "2022": 0.8}
DEFAULT_YEAR_W  = 0.5

TOP_N = 30          # papers per source per mode
PAPER_FIELDS = (    # lightweight subset written to radar_weekly.json
    "Paper_link", "Title", "_added_date", "Date",
    "Category", "_is_vlm", "code", "_tasks", "Authors",
)


def get_beijing_monday() -> str:
    """Return ISO date string of Monday of the current week in Beijing time (UTC+8)."""
    tz_bj = timezone(timedelta(hours=8))
    now = datetime.now(tz_bj)
    wd = now.weekday()          # 0=Mon … 6=Sun
    monday = now.date() - timedelta(days=wd)
    return monday.isoformat()


def load_keywords() -> dict:
    path = WORDCLOUD_DIR / "keywords.json"
    if not path.exists():
        print(f"  [warn] keywords.json not found at {path}, skipping")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_effective_keywords(keywords_data: dict, ds_key: str) -> list[dict]:
    """Merge + weight keywords across years, mirroring JS getEffectiveKeywords."""
    if not keywords_data:
        return []

    sources = (
        [k for k in keywords_data if not k.startswith("_")]
        if ds_key == "all"
        else [ds_key]
    )

    merged: dict[str, dict] = {}
    for src in sources:
        src_data = keywords_data.get(src)
        if not src_data:
            continue
        for yr, yr_data in src_data.items():
            if not yr_data or not isinstance(yr_data, dict):
                continue
            kws = yr_data.get("keywords")
            if not kws:
                continue
            yw = YEAR_WEIGHTS.get(yr, DEFAULT_YEAR_W)
            for kw in kws:
                word = kw["word"].lower()
                if word not in merged:
                    merged[word] = {"word": word, "freq": 0.0, "weight": 0.0}
                merged[word]["freq"]   += kw["freq"]   * yw
                merged[word]["weight"] += kw["weight"] * yw

    return sorted(merged.values(), key=lambda x: -x["weight"])


def score_paper(paper: dict, keywords: list[dict], mode: str) -> tuple[float, list[str]]:
    """Score a single paper, mirroring JS scorePaper."""
    text = (
        (paper.get("Title") or "") + " " + (paper.get("Abstract") or "")
    ).lower()

    score = 0.0
    matched = []
    for kw in keywords:
        if kw["word"] in text:
            score += kw["freq"] if mode == "freq" else kw["weight"]
            matched.append(kw["word"])

    if mode == "comprehensive":
        if (paper.get("code") or "").strip():
            score *= 1.3
        if paper.get("_is_vlm"):
            score *= 1.15
        if (paper.get("_tasks") or "").strip():
            score *= 1.05

    return round(score * 100) / 100, matched


def slim(paper: dict, score: float, matched: list[str]) -> dict:
    """Return only the fields needed by the radar ranking card."""
    entry = {k: paper.get(k, "") for k in PAPER_FIELDS}
    # Normalise _is_vlm — may be bool or string
    is_vlm = entry.get("_is_vlm")
    entry["_is_vlm"] = bool(is_vlm) if not isinstance(is_vlm, str) else is_vlm.lower() == "true"
    entry["score"]   = score
    entry["matched"] = matched[:6]   # keep top 6 matched keywords
    return entry


def process_source(
    src_key: str,
    filename: str,
    keywords_data: dict,
    week_from: str,
) -> dict:
    path = OUTPUT_DIR / filename
    if not path.exists():
        print(f"  [{src_key}] {filename} not found, skipped")
        return {}

    with open(path, encoding="utf-8") as f:
        papers = json.load(f)

    # Filter to current week
    week_papers = [
        p for p in papers
        if (p.get("_added_date") or "") >= week_from
    ]
    print(f"  [{src_key}] {len(papers)} total -> {len(week_papers)} this week (since {week_from})")

    if not week_papers:
        return {"paper_count": 0, "trend": [], "freq": [], "comprehensive": []}

    kws = get_effective_keywords(keywords_data, src_key)
    if not kws:
        print(f"  [{src_key}] no keywords available, skipped scoring")
        return {"paper_count": len(week_papers), "trend": [], "freq": [], "comprehensive": []}

    result: dict = {"paper_count": len(week_papers)}
    for mode in ("trend", "freq", "comprehensive"):
        scored = []
        for p in week_papers:
            s, matched = score_paper(p, kws, mode)
            if s > 0:
                scored.append((s, matched, p))

        scored.sort(key=lambda x: -x[0])
        result[mode] = [slim(p, s, m) for s, m, p in scored[:TOP_N]]

    return result


def generate() -> dict:
    week_from = get_beijing_monday()
    print(f"\nGenerating radar_weekly.json  (week_from={week_from})")

    keywords_data = load_keywords()
    if not keywords_data:
        print("  No keywords data, aborting.")
        return {}

    output: dict = {
        "_generated": date.today().isoformat(),
        "_week_from": week_from,
    }

    for src_key, filename in SOURCES.items():
        output[src_key] = process_source(src_key, filename, keywords_data, week_from)

    out_path = OUTPUT_DIR / "radar_weekly.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    print(f"\nSaved -> {out_path}  ({size_kb:.1f} KB)")
    for src in SOURCES:
        entry = output.get(src, {})
        n_trend = len(entry.get("trend", []))
        print(f"  [{src}] {entry.get('paper_count', 0)} week papers -> top {n_trend} ranked")

    return output


if __name__ == "__main__":
    generate()
