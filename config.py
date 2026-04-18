"""Configuration for arXiv remote sensing paper scraper."""

# Search parameters
SEARCH_QUERY = (
    '(ti:"remote sensing" OR abs:"remote sensing")'
    " AND ("
    "cat:eess.IV OR cat:eess.SP OR "
    "cat:cs.AI OR cat:cs.LG OR cat:cs.MM OR "
    "cat:physics.geo-ph OR cat:physics.ao-ph OR "
    "cat:stat.ML OR cat:cs.RO OR cat:cs.NE"
    ")"
)

# Date range
START_YEAR = 2020
END_YEAR = 2026

# arXiv API settings
BATCH_SIZE = 100          # max results per API call
REQUEST_DELAY = 3.0       # seconds between requests (arXiv rate limit)
MAX_RETRIES = 5           # retry on transient errors

# Papers With Code API
PWC_API_BASE = "https://paperswithcode.com/api/v1"
PWC_REQUEST_DELAY = 1.0   # seconds between PWC API requests

# Output
OUTPUT_DIR = "output"
CSV_FILENAME = "papers.csv"
JSON_FILENAME = "papers.json"

# arXiv category full names
CATEGORY_NAMES = {
    "cs.CV": "Computer Vision",
    "cs.AI": "Artificial Intelligence",
    "cs.LG": "Machine Learning",
    "cs.MM": "Multimedia",
    "cs.RO": "Robotics",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.IR": "Information Retrieval",
    "eess.IV": "Image and Video Processing",
    "eess.SP": "Signal Processing",
    "eess.AS": "Audio and Speech Processing",
    "physics.geo-ph": "Geophysics",
    "physics.ao-ph": "Atmospheric and Oceanic Physics",
    "stat.ML": "Machine Learning (Statistics)",
}
