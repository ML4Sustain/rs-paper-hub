"""Progress tracking for resumable scraping and downloading."""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PROGRESS_FILE = "progress.json"


class ProgressTracker:
    """Track scraping/downloading progress for resumable operation.

    Stores state in a JSON file:
    {
        "scrape": {
            "last_year": 2023,
            "last_month": 6,
            "total_scraped": 1234,
            "completed": false
        },
        "downloaded": ["2301.12345v1", "2302.67890v2", ...],
        "failed": ["2303.11111v1", ...],
        "updated_at": "2026-04-18T12:00:00"
    }
    """

    def __init__(self, output_dir: str):
        self.path = os.path.join(output_dir, PROGRESS_FILE)
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Corrupted progress file, starting fresh: {e}")
        return {
            "scrape": {"last_year": None, "last_month": None, "total_scraped": 0, "completed": False},
            "downloaded": [],
            "failed": [],
            "updated_at": None,
        }

    def save(self):
        self.data["updated_at"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        # Write to temp file first, then rename for atomicity
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(self.data, f, indent=2)
        os.replace(tmp_path, self.path)

    # -- Scrape progress --

    @property
    def scrape_completed(self) -> bool:
        return self.data["scrape"].get("completed", False)

    @property
    def last_scraped_year(self) -> int | None:
        return self.data["scrape"].get("last_year")

    @property
    def last_scraped_month(self) -> int | None:
        return self.data["scrape"].get("last_month")

    @property
    def total_scraped(self) -> int:
        return self.data["scrape"].get("total_scraped", 0)

    def update_scrape(self, year: int, month: int, total: int):
        self.data["scrape"]["last_year"] = year
        self.data["scrape"]["last_month"] = month
        self.data["scrape"]["total_scraped"] = total
        self.save()

    def mark_scrape_done(self, total: int):
        self.data["scrape"]["completed"] = True
        self.data["scrape"]["total_scraped"] = total
        self.save()

    def should_skip_month(self, year: int, month: int) -> bool:
        """Check if this year-month was already fully scraped."""
        last_y = self.last_scraped_year
        last_m = self.last_scraped_month
        if last_y is None or last_m is None:
            return False
        return (year, month) < (last_y, last_m)

    # -- Download progress --

    @property
    def downloaded_ids(self) -> set[str]:
        return set(self.data.get("downloaded", []))

    @property
    def failed_ids(self) -> set[str]:
        return set(self.data.get("failed", []))

    def mark_downloaded(self, arxiv_id: str):
        if arxiv_id not in self.data["downloaded"]:
            self.data["downloaded"].append(arxiv_id)
            # Remove from failed if it was there
            if arxiv_id in self.data["failed"]:
                self.data["failed"].remove(arxiv_id)

    def mark_failed(self, arxiv_id: str):
        if arxiv_id not in self.data["failed"] and arxiv_id not in self.data["downloaded"]:
            self.data["failed"].append(arxiv_id)

    def save_download_batch(self):
        """Save after a batch of downloads (avoid saving per-file for perf)."""
        self.save()

    # -- Summary --

    def summary(self) -> str:
        dl = len(self.data.get("downloaded", []))
        fail = len(self.data.get("failed", []))
        scrape = self.data["scrape"]
        parts = []
        if scrape.get("last_year"):
            status = "done" if scrape["completed"] else f"up to {scrape['last_year']}-{scrape['last_month']:02d}"
            parts.append(f"Scraped: {scrape['total_scraped']} papers ({status})")
        if dl or fail:
            parts.append(f"Downloaded: {dl}, Failed: {fail}")
        if self.data.get("updated_at"):
            parts.append(f"Last update: {self.data['updated_at']}")
        return " | ".join(parts) if parts else "No progress yet"
