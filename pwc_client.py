"""Papers With Code API client for fetching code repository links."""

import time
import logging

import requests

from config import PWC_API_BASE, PWC_REQUEST_DELAY

logger = logging.getLogger(__name__)


class PapersWithCodeClient:
    """Client for querying Papers With Code API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._cache: dict[str, str] = {}

    def get_code_url(self, arxiv_id: str) -> str:
        """
        Get the code repository URL for an arXiv paper.

        Args:
            arxiv_id: arXiv paper ID (e.g. '2301.12345' or '2301.12345v1')

        Returns:
            Code repository URL, or empty string if not found
        """
        # Normalize: strip version suffix
        clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

        if clean_id in self._cache:
            return self._cache[clean_id]

        url = f"{PWC_API_BASE}/papers/"
        try:
            # Search by arXiv ID
            resp = self.session.get(
                url, params={"arxiv_id": clean_id}, timeout=10
            )
            time.sleep(PWC_REQUEST_DELAY)

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    paper_id = results[0].get("id", "")
                    if paper_id:
                        code_url = self._get_repo_url(paper_id)
                        self._cache[clean_id] = code_url
                        return code_url

            self._cache[clean_id] = ""
            return ""

        except Exception as e:
            logger.debug(f"PWC query failed for {arxiv_id}: {e}")
            self._cache[clean_id] = ""
            return ""

    def _get_repo_url(self, paper_id: str) -> str:
        """Get the official/best repository URL for a PWC paper."""
        url = f"{PWC_API_BASE}/papers/{paper_id}/repositories/"
        try:
            resp = self.session.get(url, timeout=10)
            time.sleep(PWC_REQUEST_DELAY)

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    # Prefer official repos, then sort by stars
                    official = [r for r in results if r.get("is_official")]
                    if official:
                        return official[0].get("url", "")
                    # Fallback to most-starred
                    results.sort(key=lambda r: r.get("stars", 0), reverse=True)
                    return results[0].get("url", "")

        except Exception as e:
            logger.debug(f"PWC repo query failed for {paper_id}: {e}")

        return ""

    def enrich_papers(self, papers: list[dict], progress_callback=None) -> list[dict]:
        """
        Add code URLs to a list of paper dicts.

        Args:
            papers: List of paper dicts with 'arxiv_id' field
            progress_callback: Optional callable for progress updates

        Returns:
            Same list with 'code' field populated
        """
        for i, paper in enumerate(papers):
            arxiv_id = paper.get("arxiv_id", "")
            if arxiv_id:
                paper["code"] = self.get_code_url(arxiv_id)

            if progress_callback:
                progress_callback(i + 1, len(papers))

        return papers
