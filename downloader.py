"""Download arXiv paper PDFs to local storage with progress tracking."""

import os
import re
import time
import logging

import requests
from tqdm import tqdm

from config import REQUEST_DELAY
from progress import ProgressTracker

logger = logging.getLogger(__name__)

PDF_DIR = "pdfs"
SAVE_EVERY = 10  # save progress every N downloads


def sanitize_filename(title: str, max_len: int = 80) -> str:
    """Convert paper title to a safe filename."""
    name = re.sub(r"[^\w\s\-]", "", title)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:max_len]


def arxiv_id_to_pdf_url(paper_link: str) -> str:
    """Convert arXiv abs link to PDF download URL."""
    return paper_link.replace("/abs/", "/pdf/").replace("http://", "https://") + ".pdf"


def extract_arxiv_id(paper_link: str) -> str:
    """Extract arXiv ID from link."""
    return paper_link.split("/abs/")[-1].replace("/", "_")


def download_pdf(pdf_url: str, save_path: str, timeout: int = 30) -> bool:
    """Download a single PDF file."""
    try:
        resp = requests.get(pdf_url, timeout=timeout, stream=True)
        if resp.status_code == 200 and "application/pdf" in resp.headers.get("Content-Type", ""):
            # Download to temp file first, rename on success
            tmp_path = save_path + ".tmp"
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            os.replace(tmp_path, save_path)
            return True
        else:
            logger.warning(f"Failed to download {pdf_url}: HTTP {resp.status_code}")
            return False
    except Exception as e:
        # Clean up partial download
        tmp_path = save_path + ".tmp"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        logger.warning(f"Download error for {pdf_url}: {e}")
        return False


def download_papers(
    papers: list[dict],
    output_dir: str,
    progress: ProgressTracker | None = None,
    delay: float = REQUEST_DELAY,
    organize_by_year: bool = True,
) -> int:
    """
    Download PDFs for a list of papers with progress tracking.

    Args:
        papers: List of paper dicts with Paper_link, Title, Year fields
        output_dir: Base output directory
        progress: ProgressTracker for resumable downloads
        delay: Seconds between downloads
        organize_by_year: Create year subdirectories

    Returns:
        Number of successfully downloaded PDFs
    """
    pdf_base = os.path.join(output_dir, PDF_DIR)
    os.makedirs(pdf_base, exist_ok=True)

    # Get already-downloaded IDs from progress tracker
    already_done = progress.downloaded_ids if progress else set()

    downloaded = 0
    skipped = 0
    failed = 0
    batch_count = 0

    pbar = tqdm(
        papers,
        desc="Downloading PDFs",
        unit="pdf",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}",
    )

    for paper in pbar:
        link = paper.get("Paper_link", "")
        if not link:
            continue

        arxiv_id = extract_arxiv_id(link)

        # Skip if already tracked as downloaded
        if arxiv_id in already_done:
            skipped += 1
            pbar.set_postfix_str(f"ok:{downloaded} skip:{skipped} fail:{failed}")
            continue

        year = paper.get("Year", "unknown")
        title = paper.get("Title", "untitled")

        # Build save path
        if organize_by_year:
            save_dir = os.path.join(pdf_base, str(year))
        else:
            save_dir = pdf_base
        os.makedirs(save_dir, exist_ok=True)

        filename = f"{arxiv_id}_{sanitize_filename(title)}.pdf"
        save_path = os.path.join(save_dir, filename)

        # Skip if file already exists on disk (but not in progress tracker)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            skipped += 1
            if progress:
                progress.mark_downloaded(arxiv_id)
            pbar.set_postfix_str(f"ok:{downloaded} skip:{skipped} fail:{failed}")
            continue

        pdf_url = arxiv_id_to_pdf_url(link)
        if download_pdf(pdf_url, save_path):
            downloaded += 1
            if progress:
                progress.mark_downloaded(arxiv_id)
        else:
            failed += 1
            if progress:
                progress.mark_failed(arxiv_id)

        batch_count += 1
        pbar.set_postfix_str(f"ok:{downloaded} skip:{skipped} fail:{failed}")

        # Periodically save progress
        if progress and batch_count % SAVE_EVERY == 0:
            progress.save_download_batch()

        time.sleep(delay)

    pbar.close()

    # Final save
    if progress:
        progress.save_download_batch()

    logger.info(
        f"Download complete: {downloaded} new, {skipped} skipped, {failed} failed"
    )
    return downloaded
