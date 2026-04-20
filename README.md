<div align="center">

<img src="asset/logo.png" alt="RS-Paper-Hub" width="100">

# RS-Paper-Hub

**A curated collection of Remote Sensing & Earth Observation papers from arXiv, with automated scraping, cleaning, task tagging, VLM filtering, and Agent filtering.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/Source-arXiv-b31b1b.svg)](https://arxiv.org/)
[![Website](https://img.shields.io/badge/Website-rspaper.top-4f46e5.svg)](https://rspaper.top)
[![Team](https://img.shields.io/badge/Team-ML4Sustain-green.svg?logo=github)](https://github.com/ML4Sustain)
[![Docs](https://img.shields.io/badge/Docs-online-blue.svg)](https://rspaper.top/docs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](README.md) | [中文](README_zh.md) | [Live Demo](https://rspaper.top)

</div>

---

## Overview

RS-Paper-Hub automatically scrapes remote sensing and earth observation papers from arXiv, extracts structured metadata, and provides a one-click pipeline for data cleaning, task tagging, VLM filtering, Agent filtering, and classification. Updated daily via GitHub Actions (Mon–Fri, synced with arXiv announcement schedule).

### Key Features

- **Dual Search Scope** — Covers both "remote sensing" and "earth observation" papers from arXiv
- **Daily Automated Updates** — GitHub Actions fetches the latest papers (last 7 days) Mon–Fri at 00:30 UTC (08:30 Beijing Time), aligned with arXiv's announcement schedule
- **Incremental Pipeline** — Only new papers go through cleaning, classification, and tagging; existing data is preserved
- **Task Tagging** — Auto-tags papers with 11 task types: Classification, Object Detection, Change Detection, Segmentation, VQA, Image Captioning, Visual Grounding, Image-Text Retrieval, Geolocation, Super-Resolution, 3D Reconstruction
- **Paper Classification** — Labels papers as `Method`, `Dataset`, or `Survey` based on title keywords
- **VLM Filtering** — Keyword-based filtering for Vision-Language Model related papers with context-aware rules (avoids false positives from non-VLM cross-modal or retrieval terms)
- **Agent Filtering** — Keyword-based filtering for Agent / Autonomous Decision-Making related papers (multi-agent systems, RL-based agents, LLM agents, agentic workflows, etc.)
- **UAV Filtering** — Keyword-based filtering for UAV / drone related papers (unmanned aerial vehicles, drone-based remote sensing, aerial photogrammetry, etc.)
- **Four-Tab Web Viewer** — Browse All Papers, UAV subset, VLM subset, or Agent subset; with search, multi-dimensional chart filtering, task/category/year filters, Google Scholar links, and mobile-friendly UI
- **Clickable Tag Filtering** — Click any tag (date, type, category, task, VLM, etc.) on a paper card to filter by that value; stack multiple tags for progressive filtering, click again to remove
- **Paper Collection** — Collect papers across multiple searches into a personal collection, then view or export them together
- **BibTeX Batch Export** — Export filtered results, current page, custom range, or collection as timestamped `.bib` file with optional abstracts
- **Group Export** — Export selected papers as a Group JSON file for sharing curated reading lists; submit via PR to make it available to all users
- **Code Discovery** — Automatically extracts code repository URLs from abstracts
- **RSS/Atom Feeds** — Auto-generated Atom feeds (All / VLM / Agent) for Zotero subscription, updated daily with the last 7 days of papers
- **PDF Download** — Batch download with deduplication, organized by year

---

## Quick Start

```bash
pip install -r requirements.txt

# Scrape all papers
python main.py

# One-click: clean + classify + tag tasks + filter VLM + filter Agent
python pipeline.py
```

---

## Daily Workflow

```bash
# 1. Grab latest papers (last 7 days, incremental by default)
python main.py --update

# 2. Run full pipeline (deduplicate → clean → classify → tag → filter VLM & Agent → export)
python pipeline.py
```

That's it. All output files (`papers.csv/json`, `papers_vlm.csv/json`, `papers_agent.csv/json`) are updated in place.

> **Note:** `--incremental` is enabled by default — existing papers are always skipped. Use `--no-incremental` to force a full re-fetch.

---

## Usage

### Scraping

```bash
# Full scrape
python main.py

# Custom year range
python main.py --start-year 2023 --end-year 2025

# Limit results (for testing)
python main.py --max-results 100

# Quick update (latest 7 days)
python main.py --update

# Check progress
python main.py --status
```

### Pipeline (Recommended)

```bash
# One-click: clean + classify + tag tasks + filter VLM + filter Agent
python pipeline.py

# Custom input
python pipeline.py --input output/papers.json
```

`pipeline.py` runs the following 9 steps (incrementally — each step skips already-processed papers):

1. **Load & Deduplicate** — Remove duplicate papers by `Paper_link`
2. **Clean** — Extract code URLs from abstracts, fill `code` field
3. **Classify** — Label every paper as Method / Dataset / Survey (title-based)
4. **Tag Tasks** — Assign task labels (CLS, OD, CD, SEG, VQA, IC, VG, ITR, GeoLoc, SR, 3D)
5. **Save** — Write cleaned `papers.csv` + `papers.json`
6. **Filter VLM** — Select Vision-Language Model related papers by keyword matching
7. **Classify VLM** — Refine categories for VLM subset, export `papers_vlm.csv/json`
8. **Filter & Classify Agent** — Select Agent-related papers by keyword matching, export `papers_agent.csv/json`
9. **Generate Atom Feeds** — Produce `feed.xml`, `feed_vlm.xml`, `feed_agent.xml` with the last 7 days of papers

### Standalone Filter Scripts

```bash
# VLM filter only
python filter_vlm.py --input output/papers.json

# Agent filter only
python filter_agent.py --input output/papers.json

# Preview without saving (dry-run)
python filter_vlm.py --dry-run
python filter_agent.py --dry-run
```

### PDF Download

```bash
# Scrape + download
python main.py --download

# Download only (from existing data)
python main.py --download-only
```

---

## CLI Reference

### `main.py`

| Flag | Description | Default |
|------|-------------|---------|
| `--start-year` | Start year | 2020 |
| `--end-year` | End year | 2026 |
| `--max-results` | Max papers to fetch | unlimited |
| `--output-dir` | Output directory | `output` |
| `--update` | Quick update (latest 7 days) | off |
| `--no-incremental` | Disable incremental, re-fetch all | off |
| `--incremental` | Skip existing papers | **on** |
| `--download` | Download PDFs | off |
| `--download-only` | Download PDFs only (skip scraping) | off |
| `--with-code` | Query Papers With Code for repos | off |
| `--status` | Show progress and exit | — |
| `-v, --verbose` | Verbose logging | off |

### `pipeline.py`

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Input JSON file | `output/papers.json` |
| `--output-dir` | Output directory | `output` |

### `filter_vlm.py` / `filter_agent.py`

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Input JSON file | `output/papers.json` |
| `--output-dir` | Output directory | `output` |
| `--dry-run` | Preview matches without saving | off |

---

## Output Schema

All outputs are available in both **CSV** and **JSON** format.

| Field | Description | Example |
|-------|-------------|---------|
| `Category` | Paper category | Method, Dataset, Survey |
| `Type` | arXiv primary category | Computer Vision |
| `Subtype` | Secondary categories | Image and Video Processing |
| `Date` | Exact publication date | 2024-03-15 |
| `Month` | Publication month | 3 |
| `Year` | Publication year | 2024 |
| `Title` | Paper title | Hybrid Attention Network for... |
| `abbr.` | Abbreviation from title | HMANet |
| `Paper_link` | arXiv URL | http://arxiv.org/abs/2301.12345 |
| `Abstract` | Full abstract | ... |
| `code` | Code repository URL | https://github.com/... |
| `Publication` | Venue (journal/conference) | CVPR 2024 |
| `BibTex` | BibTeX citation | @article{...} |
| `Authors` | Author list | Alice, Bob, Charlie |
| `_tasks` | Task tags (semicolon-separated) | CLS;OD;SEG |

---

## Task Tags

Papers are automatically tagged with task types based on title and abstract keyword matching:

| Tag | Task | Examples |
|-----|------|----------|
| **CLS** | Classification | scene classification, land use/cover classification |
| **OD** | Object Detection | object/vehicle/ship/building detection |
| **CD** | Change Detection | change detection, bi-temporal analysis |
| **SEG** | Segmentation | semantic/instance/panoptic/referring segmentation |
| **VQA** | Visual Question Answering | VQA, RSVQA |
| **IC** | Image Captioning | image captioning, caption generation |
| **VG** | Visual Grounding | visual grounding, phrase grounding |
| **ITR** | Image-Text Retrieval | cross-modal retrieval |
| **GeoLoc** | Geolocation | geolocation, place recognition |
| **SR** | Super-Resolution | super-resolution, image enhancement |
| **3D** | 3D Reconstruction | 3D reconstruction, point cloud, depth estimation |

---

## Project Structure

```
rs-paper-hub/
├── main.py              # Scraper CLI entry point
├── pipeline.py          # One-click: clean + classify + tag + filter VLM & Agent + RSS
├── filter_vlm.py        # Standalone VLM filter script
├── filter_agent.py      # Standalone Agent filter script
├── filter_uav.py        # Standalone UAV filter script
├── rss_generator.py     # Atom feed generator for Zotero
├── config.py            # Search configuration
├── scraper.py           # arXiv API scraper
├── parser.py            # Metadata parser & BibTeX generation
├── downloader.py        # PDF downloader with resume support
├── progress.py          # Progress tracker
├── pwc_client.py        # Papers With Code client
├── cleaning/
│   ├── abstract_cleaner.py   # Abstract URL extraction
│   ├── classifier.py         # Paper classifier (Method/Dataset/Survey)
│   ├── task_tagger.py        # Task tagging (11 task types)
│   └── filter/
│       ├── vlm_filter.py     # VLM keyword rules
│       ├── agent_filter.py   # Agent keyword rules
│       └── uav_filter.py     # UAV keyword rules
├── .github/workflows/
│   └── daily-update.yml      # Daily CI/CD pipeline (Mon-Fri, synced with arXiv)
├── index.html               # Interactive web viewer (4 tabs: All / UAV / VLM / Agent)
├── groups/                  # Paper groups for curated reading lists
│   ├── index.json           # Group registry (key, label, file; auto+authors for auto-update)
│   └── *.json               # Individual group files (arrays of arXiv URLs)
├── update_groups.py         # Auto-update groups by author matching
├── requirements.txt
└── output/
    ├── papers.csv/json              # All papers (cleaned + classified + tagged)
    ├── papers_vlm.csv/json          # VLM subset with categories
    ├── papers_vlm_annotated.json    # Full list with VLM flags
    ├── papers_agent.csv/json        # Agent subset with categories
    ├── papers_agent_annotated.json  # Full list with Agent flags
    ├── papers_uav.csv/json          # UAV subset with categories
    ├── papers_uav_annotated.json    # Full list with UAV flags
    ├── feed.xml                     # Atom feed — all papers (last 7 days)
    ├── feed_vlm.xml                 # Atom feed — VLM papers (last 7 days)
    ├── feed_agent.xml               # Atom feed — Agent papers (last 7 days)
    ├── feed_uav.xml                 # Atom feed — UAV papers (last 7 days)
    └── progress.json                # Scraping progress
```

---

## Search Scope

Papers are fetched from **all arXiv categories** where the title or abstract contains `"remote sensing"` or `"earth observation"`. To customize, edit `SEARCH_QUERY` in [`config.py`](config.py):

```python
SEARCH_QUERY = 'ti:"remote sensing" OR abs:"remote sensing" OR ti:"earth observation" OR abs:"earth observation"'
```

---

## Web Viewer

Visit [rspaper.top](https://rspaper.top) or run locally:

```bash
python3 -m http.server 8080
```

Features include:

- **Three data tabs** — Switch between All Papers, UAV subset, VLM subset, and Agent subset
- **Quick date filters** — "Today" and "This Week" buttons with red badge counts
- **Relevance-ranked search** — Title matches prioritized over abstract matches
- **Multi-dimensional chart filtering** — Click year/type/category/task bars to filter, multi-select supported
- **Task distribution chart** — Top 5 tasks shown with collapsible remaining tasks
- **Year range selection** — Single year or custom range via dropdown
- **Paper classification** — All papers labeled as Method, Dataset, or Survey
- **Paper collection** — Collect papers across multiple searches, then view or export them together
- **BibTeX batch export** — Export filtered results, current page, custom range, or collection as timestamped `.bib` file with optional abstracts
- **Group export & sharing** — Export papers as a Group JSON file with custom name; groups appear in "All Groups" dropdown for quick filtering. Submit your group via PR to share with the community ([learn more](https://rspaper.top/docs/#submit-group))
- **Auto-updated author groups** — Define groups with `"auto": true` and `"authors": [...]` in `groups/index.json`; the pipeline automatically matches papers by author name and keeps group files up to date daily
- **New papers panel** — Side panel showing today's and this week's papers
- **Google Scholar links** — One-click search on Google Scholar for each paper
- **Bilingual UI** — Switch between English and Chinese
- **Mobile-friendly** — Responsive layout with collapsible filters and wrapping navigation
- **LaTeX rendering** — Math formulas rendered via KaTeX

> **Note:** Category and task labels are rule-based and may contain inaccuracies. We are continuously improving them. This does not affect tracking the latest research trends.

---

## RSS Feeds & Zotero Integration

The pipeline automatically generates [Atom](https://en.wikipedia.org/wiki/Atom_(web_standard)) feeds containing the last 7 days of papers. These feeds are designed for Zotero but work with any feed reader.

| Feed | URL | Content |
|------|-----|---------|
| All Papers | `https://rspaper.top/output/feed.xml` | All recent papers |
| VLM Papers | `https://rspaper.top/output/feed_vlm.xml` | VLM subset |
| Agent Papers | `https://rspaper.top/output/feed_agent.xml` | Agent subset |
| UAV Papers | `https://rspaper.top/output/feed_uav.xml` | UAV subset |

### Subscribe in Zotero

1. Open Zotero → **File** → **New Feed** → **From URL**
2. Paste one of the feed URLs above
3. Zotero will automatically pull new papers with title, authors, abstract, arXiv link, and code URL

Feeds are updated daily alongside the main pipeline via GitHub Actions.

---

## Rate Limits

| Operation | Rate | Note |
|-----------|------|------|
| Metadata query | ~3s / request | Returns up to 100 results per request |
| PDF download | ~3s / file | Respect arXiv rate limits |

**Recommended workflow**: scrape metadata first (`python main.py`), then download PDFs separately (`python main.py --download-only`).

---

## Citation

If you find RS-Paper-Hub useful in your research or work, please consider citing this repository:

```bibtex
@software{rs_paper_hub,
  author       = {ML4Sustain},
  title        = {RS-Paper-Hub: A Curated Collection of Remote Sensing and Earth Observation Papers from arXiv},
  year         = {2026},
  url          = {https://rspaper.top},
  note         = {Automated scraping, cleaning, classification, task tagging, VLM filtering, and Agent filtering pipeline for remote sensing papers}
}
```

---

## License

MIT
