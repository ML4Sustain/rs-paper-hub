"""Classify papers into Survey / Dataset / Method."""

import re


# ============================================================
# Survey — only match on title
# ============================================================
SURVEY_TITLE_PATTERNS = [
    r"\bsurvey\b",
    r"\breview\b",
    r"\boverview\b",
    r"\btutorial\b",
    r"comprehensive\s+(?:study|analysis|review|survey)",
    r"(?:systematic|literature)\s+(?:review|survey)",
    r"state[\-\s]of[\-\s]the[\-\s]art\s+(?:review|survey|overview)",
]

# ============================================================
# Dataset — primarily match on title, with a few strong abstract signals
# ============================================================
DATASET_TITLE_PATTERNS = [
    r"\bdataset\b",
    r"\bbenchmark\b",
    r"\bcorpus\b",
    r"\bannotation[s]?\b",
    r"(?:introduce|present|release|construct|build|create|propose|collect)\w*\s+(?:a\s+)?(?:new\s+)?(?:large[\-\s]scale\s+)?(?:dataset|benchmark|corpus)",
    r"(?:new|novel|large[\-\s]scale)\s+(?:dataset|benchmark|corpus)",
]

# Pre-compile
_survey_title = [re.compile(p, re.IGNORECASE) for p in SURVEY_TITLE_PATTERNS]
_dataset_title = [re.compile(p, re.IGNORECASE) for p in DATASET_TITLE_PATTERNS]


def _any_match(patterns: list[re.Pattern], text: str) -> bool:
    return any(p.search(text) for p in patterns)


def classify_paper(title: str, abstract: str) -> str:
    """
    Classify a paper into: Survey, Dataset, or Method.

    Priority: Survey (title only) > Dataset (title only) > Method (everything else)
    """
    if _any_match(_survey_title, title):
        return "Survey"

    if _any_match(_dataset_title, title):
        return "Dataset"

    return "Method"


def classify_papers(papers: list[dict]) -> list[dict]:
    """Add 'Category' field to each paper."""
    for paper in papers:
        title = str(paper.get("Title", ""))
        abstract = str(paper.get("Abstract", ""))
        paper["Category"] = classify_paper(title, abstract)
    return papers
