"""Classify VLM papers into Dataset / Method / Survey / Benchmark / Application."""

import re


# ============================================================
# Dataset 类关键词 — 标题或摘要表明论文主要贡献是数据集
# ============================================================
DATASET_TITLE_PATTERNS = [
    r"\bdataset\b",
    r"\bbenchmark\b",
    r"\bcorpus\b",
    r"\bannotation[s]?\b",
    r"(?:introduce|present|release|construct|build|create|propose|collect)\w*\s+(?:a\s+)?(?:new\s+)?(?:large[\-\s]scale\s+)?(?:dataset|benchmark|corpus)",
    r"(?:new|novel|large[\-\s]scale)\s+(?:dataset|benchmark|corpus)",
]

DATASET_ABSTRACT_PATTERNS = [
    r"(?:we|this\s+paper)\s+(?:introduce|present|release|construct|build|create|propose|collect)\w*\s+(?:a\s+)?(?:new\s+)?(?:large[\-\s]scale\s+)?(?:dataset|benchmark|corpus)",
    r"(?:annotated|labeled|labelled)\s+(?:dataset|samples|images|pairs)",
    r"(?:training|test|evaluation)\s+(?:set|split|data)\s+(?:contain|consist|compris)",
    r"\d+[kKmM]?\s+(?:image|sample|pair|instance|scene)s?\s+(?:are\s+)?(?:collected|annotated|labeled)",
    r"publicly\s+available\s+(?:dataset|benchmark)",
]

# ============================================================
# Survey / Review 类
# ============================================================
SURVEY_PATTERNS = [
    r"\bsurvey\b",
    r"\breview\b",
    r"\boverview\b",
    r"\btutorial\b",
    r"comprehensive\s+(?:study|analysis|review|survey)",
    r"(?:systematic|literature)\s+(?:review|survey)",
    r"state[\-\s]of[\-\s]the[\-\s]art\s+(?:review|survey|overview)",
]

# ============================================================
# Method 类关键词 — 论文主要贡献是提出新方法/模型/网络
# ============================================================
METHOD_TITLE_PATTERNS = [
    r"\bnetwork\b",
    r"\bmodel\b",
    r"\bframework\b",
    r"\barchitecture\b",
    r"\bmodule\b",
    r"\bapproach\b",
    r"\bmethod\b",
    r"\bstrategy\b",
    r"\balgorithm\b",
    r"\blearning\b",
    r"\bNet\b",
    r"\bGAN\b",
    r"\btransformer\b",
    r"\battention\b",
    r"\bdiffusion\b",
    r"\bprompt\b",
]

METHOD_ABSTRACT_PATTERNS = [
    r"(?:we|this\s+paper)\s+(?:propose|present|introduce|design|develop)\w*\s+(?:a\s+)?(?:new\s+|novel\s+)?(?:method|approach|framework|model|network|module|architecture|strategy|algorithm|pipeline|scheme|mechanism|technique)",
    r"(?:our|the\s+proposed)\s+(?:method|approach|framework|model|network)",
    r"(?:new|novel)\s+(?:method|approach|framework|model|network|module|architecture|strategy|algorithm)",
    r"(?:outperform|surpass|exceed|achieve\s+state[\-\s]of[\-\s]the[\-\s]art|achieve\s+superior)",
    r"experiment\w*\s+(?:show|demonstrate|indicate|reveal|prove|verify|validate)",
]

# ============================================================
# Application 类 — 应用落地，不是提新方法也不是新数据集
# ============================================================
APPLICATION_PATTERNS = [
    r"(?:case\s+study|real[\-\s]world\s+application|practical\s+application|deployment)",
    r"(?:applied|applying)\s+(?:to|for|in)\s+(?:urban|agriculture|disaster|flood|wildfire|forest|crop|building|land[\-\s]?use|land[\-\s]?cover)",
]

# Pre-compile
_dataset_title = [re.compile(p, re.IGNORECASE) for p in DATASET_TITLE_PATTERNS]
_dataset_abstract = [re.compile(p, re.IGNORECASE) for p in DATASET_ABSTRACT_PATTERNS]
_survey = [re.compile(p, re.IGNORECASE) for p in SURVEY_PATTERNS]
_method_title = [re.compile(p, re.IGNORECASE) for p in METHOD_TITLE_PATTERNS]
_method_abstract = [re.compile(p, re.IGNORECASE) for p in METHOD_ABSTRACT_PATTERNS]
_application = [re.compile(p, re.IGNORECASE) for p in APPLICATION_PATTERNS]


def _any_match(patterns: list[re.Pattern], text: str) -> bool:
    return any(p.search(text) for p in patterns)


def _count_match(patterns: list[re.Pattern], text: str) -> int:
    return sum(1 for p in patterns if p.search(text))


def classify_paper(title: str, abstract: str) -> str:
    """
    Classify a paper into one of: Dataset, Method, Survey, Application, Other.

    Priority: Survey > Dataset > Method > Application > Other
    A paper can be both Dataset and Method — in that case labeled "Dataset+Method".
    """
    is_survey = _any_match(_survey, title) or _any_match(_survey, abstract)
    if is_survey:
        return "Survey"

    # Dataset detection: stronger signal from title, weaker from abstract alone
    is_dataset_title = _any_match(_dataset_title, title)
    is_dataset_abstract = _count_match(_dataset_abstract, abstract) >= 1
    is_dataset = is_dataset_title or is_dataset_abstract

    # Method detection
    is_method_title = _count_match(_method_title, title) >= 1
    is_method_abstract = _count_match(_method_abstract, abstract) >= 2
    is_method = is_method_title or is_method_abstract

    if is_dataset and is_method:
        return "Dataset+Method"
    if is_dataset:
        return "Dataset"
    if is_method:
        return "Method"

    is_app = _any_match(_application, title) or _any_match(_application, abstract)
    if is_app:
        return "Application"

    return "Other"


def classify_papers(papers: list[dict]) -> list[dict]:
    """Add 'Category' field to each paper."""
    for paper in papers:
        title = str(paper.get("Title", ""))
        abstract = str(paper.get("Abstract", ""))
        paper["Category"] = classify_paper(title, abstract)
    return papers
