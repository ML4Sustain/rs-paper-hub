"""Filter papers related to Hyperspectral / Multispectral imaging in Remote Sensing."""

import re

# ============================================================
# Keyword lists
# ============================================================

# 核心概念关键词 — 高光谱/多光谱直接表述（命中即入选）
CORE_KEYWORDS = [
    r"\bhyperspectral\b",
    r"\bmultispectral\b",
    r"spectral\s+unmixing",
    r"endmember\s+(?:extraction|identification|estimation)",
    r"abundance\s+(?:estimation|mapping|reconstruction)",
    r"pan[\-\s]?sharpening",
    r"spectral\s+super[\-\s]?resolution",
    r"\bHSI\b.{0,20}(?:classification|detection|unmixing|data|image|sensor|remote)",
    r"\bMSI\b.{0,20}(?:fusion|classification|multispectral|remote|satellite|image)",
]

# 高光谱/多光谱传感器与卫星平台
SENSOR_KEYWORDS = [
    r"\bAVIRIS\b",
    r"\bHyperion\b.{0,20}(?:satellite|hyperspectral|EO[\-\s]?1|image|data)",
    r"\bPRISMA\b.{0,20}(?:satellite|hyperspectral|ASI|image|data)",
    r"\bDESIS\b",
    r"\bEnMAP\b",
    r"\bSentinel[\-\s]?2\b",
    r"\bLandsat\b",
    r"\bMODIS\b",
    r"\bASTER\b.{0,20}(?:satellite|remote\s+sensing|thermal|image|VNIR|SWIR|TIR)",
    r"\bWorldView[\-\s]?\d\b",
    r"\bPlanetScope\b",
    r"\bGaoFen[\-\s]?5\b",
    r"\bGF[\-\s]?5\b",
    r"\bZhuhai[\-\s]?1\b",
    r"\bIndian\s+Pines\b",
    r"\bPavia\s+(?:University|Centre|Center)\b",
    r"\bSalinas\b.{0,20}(?:hyperspectral|dataset|scene|HSI)",
]

# 高光谱/多光谱应用与任务关键词
TASK_KEYWORDS = [
    r"band\s+selection",
    r"spectral[\-\s]spatial\s+(?:classification|feature|learning|fusion)",
    r"dimensionality\s+reduction.{0,20}(?:hyperspectral|spectral|HSI)",
    r"(?:hyperspectral|multispectral|HSI).{0,20}dimensionality\s+reduction",
    r"(?:hyperspectral|multispectral).{0,20}anomaly\s+detection",
    r"anomaly\s+detection.{0,20}(?:hyperspectral|multispectral|HSI)",
    r"hyperspectral\s+(?:change\s+detection|target\s+detection|compressed\s+sensing)",
    r"multispectral[\-\s]hyperspectral\s+(?:fusion|registration|matching)",
    r"hyperspectral[\-\s]multispectral\s+(?:fusion|registration|matching)",
    r"spectral\s+(?:feature|signature|response|reflectance).{0,20}(?:remote\s+sensing|image|sensor)",
    r"spectral\s+index.{0,20}(?:vegetation|water|land|soil|building|urban)",
    r"vegetation\s+(?:mapping|monitoring|analysis|classification).{0,20}(?:satellite|remote\s+sensing|spectral|hyperspectral|multispectral)",
    r"(?:satellite|remote\s+sensing).{0,20}vegetation\s+(?:mapping|monitoring|analysis)",
    r"\bNDVI\b",
    r"\bNDWI\b",
    r"land\s+(?:cover|use)\s+(?:classification|mapping).{0,30}(?:hyperspectral|multispectral|Landsat|Sentinel|MODIS|satellite)",
    r"(?:hyperspectral|multispectral|Landsat|Sentinel|MODIS).{0,30}land\s+(?:cover|use)\s+(?:classification|mapping)",
]

# 全部合并
ALL_KEYWORDS = CORE_KEYWORDS + SENSOR_KEYWORDS + TASK_KEYWORDS

# 预编译
_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in ALL_KEYWORDS]


def is_hyperspectral_related(title: str, abstract: str) -> tuple[bool, list[str]]:
    """
    Check if a paper is related to Hyperspectral / Multispectral imaging.

    Returns:
        (is_match, matched_keywords)
    """
    text = f"{title} {abstract}"
    matched = []

    for pattern, keyword in zip(_PATTERNS, ALL_KEYWORDS):
        if pattern.search(text):
            matched.append(keyword)

    return len(matched) > 0, matched


def filter_hyperspectral_papers(papers: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Filter papers related to Hyperspectral / Multispectral imaging.

    Returns:
        (matched_papers, all_papers_with_hyp_flag)
        - matched_papers: only HSI/MSI-related papers (with _hyp_keywords field)
        - all_papers_with_hyp_flag: all papers with _is_hyp and _hyp_keywords fields
    """
    matched = []
    annotated = []

    for paper in papers:
        title = str(paper.get("Title", ""))
        abstract = str(paper.get("Abstract", ""))
        is_match, keywords = is_hyperspectral_related(title, abstract)

        paper_copy = dict(paper)
        paper_copy["_is_hyp"] = is_match
        paper_copy["_hyp_keywords"] = "; ".join(keywords) if keywords else ""
        annotated.append(paper_copy)

        if is_match:
            matched.append(paper_copy)

    return matched, annotated
