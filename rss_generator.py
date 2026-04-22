#!/usr/bin/env python3
"""
Generate Atom XML feeds from paper datasets for Zotero subscription.

Produces three feeds (last 7 days):
  - feed.xml         All papers
  - feed_vlm.xml     VLM-related papers
  - feed_agent.xml   Agent-related papers
"""

import os
import logging
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

logger = logging.getLogger(__name__)

ATOM_NS = "http://www.w3.org/2005/Atom"
SITE_URL = "https://rspaper.top"


def _parse_date(paper: dict) -> datetime | None:
    """Try to parse a paper's Date field into a datetime."""
    raw = paper.get("Date", "")
    if not raw or str(raw) in ("", "nan"):
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m"):
        try:
            return datetime.strptime(str(raw).strip(), fmt)
        except ValueError:
            continue
    return None


def _filter_recent(papers: list[dict], days: int) -> list[dict]:
    """Return papers from the last N days, sorted newest-first."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for p in papers:
        dt = _parse_date(p)
        if dt and dt >= cutoff:
            recent.append((dt, p))
    recent.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in recent]


def _build_entry_content(paper: dict) -> str:
    """Build HTML content block with extra metadata."""
    parts = []
    code = paper.get("code", "")
    if code and str(code) not in ("", "nan"):
        parts.append(f'<p><strong>Code:</strong> <a href="{code}">{code}</a></p>')
    pub = paper.get("Publication", "")
    if pub and str(pub) not in ("", "nan"):
        parts.append(f"<p><strong>Publication:</strong> {pub}</p>")
    cat = paper.get("Category", "")
    if cat and str(cat) not in ("", "nan"):
        parts.append(f"<p><strong>Category:</strong> {cat}</p>")
    tasks = paper.get("_tasks", "")
    if tasks and str(tasks) not in ("", "nan"):
        parts.append(f"<p><strong>Tasks:</strong> {tasks}</p>")
    return "\n".join(parts)


def _generate_atom_feed(
    papers: list[dict],
    feed_title: str,
    feed_id: str,
    feed_link: str,
    output_path: str,
    days: int = 7,
):
    """Generate a single Atom feed XML file."""
    recent = _filter_recent(papers, days)

    feed = Element("feed", xmlns=ATOM_NS)
    SubElement(feed, "title").text = feed_title
    SubElement(feed, "id").text = feed_id
    SubElement(feed, "link", href=feed_link, rel="self", type="application/atom+xml")
    SubElement(feed, "link", href=SITE_URL, rel="alternate", type="text/html")
    SubElement(feed, "updated").text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    SubElement(feed, "subtitle").text = (
        f"Latest remote sensing papers (last {days} days) — {len(recent)} entries"
    )

    author = SubElement(feed, "author")
    SubElement(author, "name").text = "RS-Paper-Hub"
    SubElement(author, "uri").text = SITE_URL

    for paper in recent:
        entry = SubElement(feed, "entry")

        SubElement(entry, "title").text = paper.get("Title", "Untitled")

        link = paper.get("Paper_link", "")
        SubElement(entry, "link", href=link, rel="alternate", type="text/html")
        SubElement(entry, "id").text = link

        dt = _parse_date(paper)
        if dt:
            ts = dt.strftime("%Y-%m-%dT00:00:00Z")
            SubElement(entry, "published").text = ts
            SubElement(entry, "updated").text = ts

        # Authors
        authors_str = paper.get("Authors", "")
        if authors_str and str(authors_str) not in ("", "nan"):
            for name in str(authors_str).split(","):
                name = name.strip()
                if name:
                    a = SubElement(entry, "author")
                    SubElement(a, "name").text = name

        # Abstract as summary
        abstract = paper.get("Abstract", "")
        if abstract and str(abstract) not in ("", "nan"):
            summary = SubElement(entry, "summary", type="text")
            summary.text = str(abstract)

        # Rich content with extra metadata
        content_html = _build_entry_content(paper)
        if content_html:
            content = SubElement(entry, "content", type="html")
            content.text = content_html

        # arXiv categories
        ptype = paper.get("Type", "")
        if ptype and str(ptype) not in ("", "nan"):
            SubElement(entry, "category", term=str(ptype))
        subtype = paper.get("Subtype", "")
        if subtype and str(subtype) not in ("", "nan"):
            SubElement(entry, "category", term=str(subtype))

    indent(feed, space="  ")
    tree = ElementTree(feed)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    logger.info(f"  -> {output_path} ({len(recent)} entries)")


def generate_feeds(
    all_papers: list[dict],
    vlm_papers: list[dict],
    agent_papers: list[dict],
    uav_papers: list[dict],
    output_dir: str,
    site_url: str = SITE_URL,
    days: int = 7,
    sar_papers: list[dict] | None = None,
):
    """Generate all Atom feeds."""
    global SITE_URL
    SITE_URL = site_url

    feeds = [
        (all_papers, "RS-Paper-Hub — All Papers", "feed.xml"),
        (vlm_papers, "RS-Paper-Hub — VLM Papers", "feed_vlm.xml"),
        (agent_papers, "RS-Paper-Hub — Agent Papers", "feed_agent.xml"),
        (uav_papers, "RS-Paper-Hub — UAV Papers", "feed_uav.xml"),
    ]
    if sar_papers is not None:
        feeds.append((sar_papers, "RS-Paper-Hub — SAR Papers", "feed_sar.xml"))

    for papers, title, filename in feeds:
        out_path = os.path.join(output_dir, filename)
        feed_url = f"{site_url}/output/{filename}"
        _generate_atom_feed(
            papers,
            feed_title=title,
            feed_id=feed_url,
            feed_link=feed_url,
            output_path=out_path,
            days=days,
        )

    logger.info(f"RSS feeds generated ({days}-day window)")
