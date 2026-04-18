"""Parse arXiv results into structured paper records."""

import re
import logging

import arxiv

from config import CATEGORY_NAMES

logger = logging.getLogger(__name__)


def extract_abbreviation(title: str) -> str:
    """Extract abbreviation from title, e.g. 'Some Method (SM)' -> 'SM'."""
    # Match content in parentheses that looks like an abbreviation
    # (2-10 uppercase letters, possibly with digits or hyphens)
    matches = re.findall(r"\(([A-Z][A-Za-z0-9\-]{0,9})\)", title)
    if matches:
        # Return the last abbreviation found (usually the method name)
        return matches[-1]
    return ""


def extract_publication(comment: str | None) -> str:
    """Extract publication venue from arXiv comment field."""
    if not comment:
        return ""

    # Common patterns: "Accepted at CVPR 2023", "Published in IEEE TGRS",
    # "NeurIPS 2023", "ICCV 2023 Workshop"
    venue_patterns = [
        r"(?:accepted|published|appear|to appear)\s+(?:at|in|by)\s+(.+?)(?:\.|,|$)",
        r"((?:CVPR|ICCV|ECCV|NeurIPS|ICML|AAAI|IJCAI|ICLR|ACM MM|WACV|BMVC|"
        r"IEEE\s+\w+|ISPRS|GRSL|TGRS|Remote Sensing|GeoAI|EarthVision)"
        r"[^.,]*\d{4})",
        r"(\d+\s+pages?,?\s*\d*\s*figures?)",
    ]

    for pattern in venue_patterns:
        match = re.search(pattern, comment, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return comment.strip()


def extract_institute(result: arxiv.Result) -> str:
    """
    Extract first author's institute/affiliation.
    arXiv API provides limited affiliation data; we try what's available.
    """
    # The arxiv library may expose affiliations through authors
    if result.authors:
        first_author = result.authors[0]
        # Some arXiv entries embed affiliation in author name field
        name = str(first_author)
        affil_match = re.search(r"\((.+?)\)", name)
        if affil_match:
            return affil_match.group(1)
    return ""


def get_category_type(primary_category: str) -> str:
    """Map arXiv category to a human-readable type."""
    return CATEGORY_NAMES.get(primary_category, primary_category)


def get_subtype(categories: list[str], primary: str) -> str:
    """Get secondary categories as subtype."""
    others = [c for c in categories if c != primary]
    if others:
        return "; ".join(CATEGORY_NAMES.get(c, c) for c in others[:3])
    return ""


def generate_bibtex(result: arxiv.Result) -> str:
    """Generate BibTeX entry from arXiv result."""
    # Create a citation key: first_author_last_name + year + first_word_of_title
    authors = result.authors
    if authors:
        first_last = str(authors[0]).split()[-1].lower()
        first_last = re.sub(r"[^a-z]", "", first_last)
    else:
        first_last = "unknown"

    year = result.published.year
    title_word = re.sub(r"[^a-z]", "", result.title.split()[0].lower()) if result.title else "untitled"
    cite_key = f"{first_last}{year}{title_word}"

    author_str = " and ".join(str(a) for a in authors)

    # Extract arXiv ID
    arxiv_id = result.entry_id.split("/abs/")[-1]

    bibtex = (
        f"@article{{{cite_key},\n"
        f"  title={{{result.title}}},\n"
        f"  author={{{author_str}}},\n"
        f"  journal={{arXiv preprint arXiv:{arxiv_id}}},\n"
        f"  year={{{year}}},\n"
        f"  url={{{result.entry_id}}}\n"
        f"}}"
    )
    return bibtex


def parse_result(result: arxiv.Result) -> dict:
    """Convert an arxiv.Result into a structured dict."""
    primary_cat = result.primary_category
    categories = [c for c in result.categories]

    return {
        "Type": get_category_type(primary_cat),
        "Subtype": get_subtype(categories, primary_cat),
        "Month": result.published.month,
        "Year": result.published.year,
        "Institute": extract_institute(result),
        "Title": result.title.replace("\n", " ").strip(),
        "abbr.": extract_abbreviation(result.title),
        "Paper_link": result.entry_id,
        "Abstract": result.summary.replace("\n", " ").strip(),
        "code": "",  # filled later by pwc_client
        "Publication": extract_publication(getattr(result, "comment", None)),
        "BibTex": generate_bibtex(result),
        "arxiv_id": result.entry_id.split("/abs/")[-1],
        "Authors": ", ".join(str(a) for a in result.authors),
    }


def parse_results(results: list[arxiv.Result]) -> list[dict]:
    """Parse a list of arXiv results into structured records."""
    papers = []
    for r in results:
        try:
            papers.append(parse_result(r))
        except Exception as e:
            logger.warning(f"Failed to parse {r.entry_id}: {e}")
    return papers
