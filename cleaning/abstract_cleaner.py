"""Clean abstracts: extract code URLs and fill into code field. Do NOT modify abstract text."""

import re

# URL pattern
URL_PATTERN = re.compile(
    r'https?://[^\s,;\'"<>\[\]{}()]+(?:\([^\s)]*\))*[^\s.,;\'"<>\[\]{}():]'
    r'|https?://[^\s,;\'"<>\[\]{}()]+'
)

# Code repository hosts
CODE_HOST_PATTERNS = [
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "huggingface.co",
    "codeberg.org",
    "zenodo.org",
    "kaggle.com",
]


def is_code_url(url: str) -> bool:
    url_lower = url.lower()
    return any(host in url_lower for host in CODE_HOST_PATTERNS)


def clean_url(url: str) -> str:
    url = url.rstrip(".,;:!?)}]>\"'")
    url = re.sub(r'\\[{}]', '', url)
    return url


def clean_abstract(row: dict) -> dict:
    """
    Extract code URLs from abstract and fill into code field.
    Abstract text is NOT modified.
    """
    abstract = row.get("Abstract", "")
    current_code = row.get("code", "")

    if not abstract or not isinstance(abstract, str):
        return row

    urls = [clean_url(m) for m in URL_PATTERN.findall(abstract)]
    if not urls:
        return row

    code_urls = [u for u in urls if is_code_url(u)]

    # Fill code field if empty
    if (not current_code or str(current_code) in ("nan", "")) and code_urls:
        row["code"] = code_urls[0]

    return row
