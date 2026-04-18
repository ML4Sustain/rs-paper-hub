<div align="center">

<img src="asset/logo.png" alt="RS-Paper-Hub" width="100">

# RS-Paper-Hub

**A curated collection of Remote Sensing & Earth Observation papers from arXiv, with automated scraping, cleaning, task tagging, and VLM filtering.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/source-arXiv-b31b1b.svg)](https://arxiv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Website](https://img.shields.io/badge/website-rspaper.top-4f46e5.svg)](https://rspaper.top)

[English](README.md) | [中文](README_zh.md) | [Live Demo](https://rspaper.top)

</div>

---

## Overview

RS-Paper-Hub automatically scrapes remote sensing and earth observation papers from arXiv, extracts structured metadata, and provides a one-click pipeline for data cleaning, task tagging, VLM filtering, and classification. Updated daily via GitHub Actions.

### Key Features

- **Dual Search Scope** — Covers both "remote sensing" and "earth observation" papers from arXiv
- **Daily Automated Updates** — GitHub Actions fetches the latest papers (last 7 days) every day
- **Incremental Pipeline** — Only new papers go through cleaning, classification, and tagging; existing data is preserved
- **Task Tagging** — Auto-tags papers with 11 task types: Classification, Object Detection, Change Detection, Segmentation, VQA, Image Captioning, Visual Grounding, Image-Text Retrieval, Geolocation, Super-Resolution, 3D Reconstruction
- **Paper Classification** — Labels papers as `Method`, `Dataset`, or `Survey` based on title keywords
- **VLM Filtering** — Keyword-based filtering for Vision-Language Model related papers (1000+ papers identified)
- **Interactive Web Viewer** — Search, multi-dimensional chart filtering, task/category/year filters, Google Scholar links, and mobile-friendly UI
- **Paper Collection** — Collect papers across multiple searches into a personal collection, then view or export them together
- **BibTeX Batch Export** — Export filtered results, current page, custom range, or collection as `.bib` file with optional abstracts
- **Code Discovery** — Automatically extracts code repository URLs from abstracts
- **PDF Download** — Batch download with deduplication, organized by year

---

## Quick Start

```bash
pip install -r requirements.txt

# Scrape all papers
python main.py

# One-click: clean + classify + tag tasks + filter VLM
python pipeline.py
```

---

## Daily Workflow

```bash
# 1. Grab latest papers (last 7 days, incremental by default)
python main.py --update

# 2. Run full pipeline (deduplicate → clean → classify → tag → filter → export)
python pipeline.py
```

That's it. All output files (`papers.csv/json`, `papers_vlm.csv/json`) are updated in place.

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
# One-click: clean + classify + tag tasks + VLM filter
python pipeline.py

# Custom input
python pipeline.py --input output/papers.json
```

`pipeline.py` runs the following steps (incrementally — each step skips already-processed papers):

1. **Load & Deduplicate** — Remove duplicate papers by `Paper_link`
2. **Clean** — Extract code URLs from abstracts, fill `code` field
3. **Classify** — Label every paper as Method / Dataset / Survey (title-based)
4. **Tag Tasks** — Assign task labels (CLS, OD, CD, SEG, VQA, IC, VG, ITR, GeoLoc, SR, 3D)
5. **Save** — Write cleaned `papers.csv` + `papers.json`
6. **Filter VLM** — Select VLM-related papers by keyword matching
7. **Classify VLM** — Refine categories for VLM subset
8. **Export** — Write `papers_vlm.csv/json` and `papers_vlm_annotated.json`

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
├── pipeline.py          # One-click: clean + classify + tag + filter
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
│       └── vlm_filter.py     # VLM keyword rules
├── .github/workflows/
│   └── daily-update.yml      # Daily CI/CD pipeline
├── index.html               # Interactive web viewer
├── requirements.txt
└── output/
    ├── papers.csv/json            # All papers (cleaned + classified + tagged)
    ├── papers_vlm.csv/json        # VLM subset with categories
    ├── papers_vlm_annotated.json  # Full list with VLM flags
    └── progress.json              # Scraping progress
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

- **Quick date filters** — "Today" and "This Week" buttons with red badge counts
- **Relevance-ranked search** — Title matches prioritized over abstract matches
- **Multi-dimensional chart filtering** — Click year/type/category/task bars to filter, multi-select supported
- **Task distribution chart** — Top 5 tasks shown with collapsible remaining tasks
- **Year range selection** — Single year or custom range via dropdown
- **Paper classification** — All papers labeled as Method, Dataset, or Survey
- **Paper collection** — Collect papers across multiple searches, then view or export them together
- **BibTeX batch export** — Export filtered results, current page, custom range, or collection as `.bib` file with optional abstracts
- **New papers panel** — Side panel showing today's and this week's papers
- **Google Scholar links** — One-click search on Google Scholar for each paper
- **Mobile-friendly** — Responsive layout with collapsible filters and wrapping navigation
- **LaTeX rendering** — Math formulas rendered via KaTeX

> **Note:** Category and task labels are rule-based and may contain inaccuracies. We are continuously improving them. This does not affect tracking the latest research trends.

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
  year         = {2025},
  url          = {https://rspaper.top},
  note         = {Automated scraping, cleaning, classification, task tagging, and VLM filtering pipeline for remote sensing papers}
}
```

---

## License

MIT
