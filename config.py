"""Configuration for arXiv remote sensing paper scraper."""

# Search parameters
# Search parameters — 不限分类，全量搜索
SEARCH_QUERY = 'ti:"remote sensing" OR abs:"remote sensing" OR ti:"earth observation" OR abs:"earth observation" OR ti:"geospatial" OR abs:"geospatial"'

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
