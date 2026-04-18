"""Filter papers related to Vision-Language Models (VLMs)."""

import re

# ============================================================
# Keyword lists - 宁可多选不要漏掉
# ============================================================

# 核心概念关键词（命中即入选）
CORE_KEYWORDS = [
    # VLM 直接表述
    r"vision[\-\s]language",
    r"visual[\-\s]language",
    r"vision[\-\s]and[\-\s]language",
    r"\bVLM\b",
    r"\bVLMs\b",
    r"multimodal\s+large\s+language",
    r"multimodal\s+language\s+model",
    r"multi[\-\s]modal\s+large\s+language",
    r"multi[\-\s]modal\s+language\s+model",
    r"large\s+multimodal\s+model",
    r"\bLMM\b",
    r"\bLMMs\b",
    r"\bMLLM\b",
    r"\bMLLMs\b",
    r"visual\s+foundation\s+model",
    r"vision\s+foundation\s+model",
    # 图文对齐/融合 — 遥感场景下 image+text 同时出现基本就是 VLM 相关
    r"image[\-\s]text",
    r"text[\-\s]image",
    r"image[\-\s]to[\-\s]text",
    r"text[\-\s]to[\-\s]image",
    r"\bretrieval\b",
    r"cross[\-\s]modal",
    r"vision[\-\s]text",
    r"visual[\-\s]text",
    r"image[\-\s]language",
    r"image[\-\s]text\s+pre[\-\s]?train",
    r"contrastive\s+language[\-\s]image",
    r"language[\-\s]image\s+pre[\-\s]?train",
    # Prompt / instruction tuning with vision
    r"visual\s+instruction\s+tuning",
    r"visual\s+prompt",
    r"text\s+prompt.*(?:visual|image|remote\s+sensing)",
    r"language[\-\s]guided",
    r"language[\-\s]driven",
    r"text[\-\s]guided",
    r"text[\-\s]driven",
    r"text\s+supervision.*(?:image|visual|remote)",
    r"language\s+supervision.*(?:image|visual|remote)",
    # Grounding / referring
    r"visual\s+grounding",
    r"referring.*(?:remote\s+sensing|aerial|satellite)",
    r"referring\s+expression",
    r"grounded\s+(?:language|understanding|recognition)",
    r"phrase\s+grounding",
    # Open-vocabulary / zero-shot with language
    r"open[\-\s]vocabulary",
    r"open[\-\s]world\s+(?:detection|segmentation|recognition)",
    r"zero[\-\s]shot.*(?:classif|detect|segment|recogni)",
]

# 知名模型名（命中即入选）
MODEL_KEYWORDS = [
    r"\bCLIP\b",
    r"\bCLIP[\-\s]based\b",
    r"\bOpenCLIP\b",
    r"\bRemoteCLIP\b",
    r"\bGeoRSCLIP\b",
    r"\bSigLIP\b",
    r"\bALIGN\s+model\b",
    r"\bBLIP\b",
    r"\bBLIP[\-\s]2\b",
    r"\bInstructBLIP\b",
    r"\bLLaVA\b",
    r"\bMiniGPT\b",
    r"\bGPT[\-\s]4[Vv]\b",
    r"\bGPT[\-\s]4o\b",
    r"\bGemini\b",
    r"\bChatGPT\b",
    r"\bFlamingo\b",
    r"\bOpenFlamingo\b",
    r"\bQwen[\-\s]VL\b",
    r"\bInternVL\b",
    r"\bCogVLM\b",
    r"\bGroundingDINO\b",
    r"\bGrounding\s+DINO\b",
    r"\bSegment\s+Anything\b",
    r"\bSAM[\-\s]based\b",
    r"\bHQ[\-\s]SAM\b",
    r"\bRSPrompter\b",
    r"\bOWL[\-\s]ViT\b",
    r"\bLSeg\b",
    r"\bCLIPSeg\b",
    r"\bX[\-\s]Decoder\b",
    r"\bSEEM\b",
    r"\bOPEN[\-\s]SEG\b",
    r"\bStable\s+Diffusion\b",
    r"\bDALL[\-\s]?E\b",
    r"\bFlorence\b",
    r"\bBEiT[\-\s]?3\b",
    r"\bCoCa\b",
    r"\bEVA[\-\s]CLIP\b",
    r"\bAlpha[\-\s]CLIP\b",
    r"\bConvCLIP\b",
    r"\bRegionCLIP\b",
    r"\bPointCLIP\b",
    r"\bRS[\-\s]?CLIP\b",
    r"\bSkyCLIP\b",
    r"\bGeoChat\b",
    r"\bSkyEyeGPT\b",
    r"\bEarthGPT\b",
    r"\bRSGPT\b",
    r"\bH2RSVLM\b",
    r"\bLHRS[\-\s]Bot\b",
    r"\bSpatialRGPT\b",
    r"\bGeoLLM\b",
]

# 相关任务关键词（命中即入选）
TASK_KEYWORDS = [
    r"visual\s+question\s+answering",
    r"\bVQA\b",
    r"\bRSVQA\b",
    r"image\s+captioning",
    r"remote\s+sensing\s+captioning",
    r"image[\-\s]text\s+retrieval",
    r"text[\-\s]to[\-\s]image",
    r"image[\-\s]to[\-\s]text",
    r"scene\s+(?:description|understanding|caption|text)",
    r"visual\s+reasoning",
    r"visual\s+dialog",
    r"change\s+captioning",
    r"dense\s+captioning",
    r"grounding\s+(?:detection|segmentation)",
    # RS-specific VLM tasks
    r"referring.*(?:segmentation|expression|detection).*(?:remote|aerial|satellite)",
    r"(?:remote|aerial|satellite).*referring.*(?:segmentation|expression|detection)",
    r"remote\s+sensing\s+image\s+(?:text|caption|description)",
    r"(?:aerial|satellite)\s+image\s+(?:text|caption|description)",
    r"text[\-\s]based\s+(?:remote\s+sensing|aerial|satellite)",
    r"language[\-\s]aware.*(?:remote|aerial|satellite|detection|segmentation)",
    r"visual\s+entailment",
    r"visual[\-\s]semantic",
    r"image[\-\s]sentence",
    r"sentence[\-\s]image",
    r"(?:image|visual)\s+(?:and|&)\s+(?:text|language)\s+(?:understanding|generation|matching|alignment)",
]

# 全部合并
ALL_KEYWORDS = CORE_KEYWORDS + MODEL_KEYWORDS + TASK_KEYWORDS

# 预编译
_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in ALL_KEYWORDS]


def is_vlm_related(title: str, abstract: str) -> tuple[bool, list[str]]:
    """
    Check if a paper is related to Vision-Language Models.

    Args:
        title: Paper title
        abstract: Paper abstract

    Returns:
        (is_match, matched_keywords) - whether it matches and which keywords hit
    """
    text = f"{title} {abstract}"
    matched = []

    for pattern, keyword in zip(_PATTERNS, ALL_KEYWORDS):
        if pattern.search(text):
            matched.append(keyword)

    return len(matched) > 0, matched


def filter_vlm_papers(papers: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Filter papers related to VLMs.

    Returns:
        (matched_papers, all_papers_with_vlm_flag)
        - matched_papers: only VLM-related papers (with _vlm_keywords field)
        - all_papers_with_vlm_flag: all papers with _is_vlm and _vlm_keywords fields added
    """
    matched = []
    annotated = []

    for paper in papers:
        title = str(paper.get("Title", ""))
        abstract = str(paper.get("Abstract", ""))
        is_match, keywords = is_vlm_related(title, abstract)

        paper_copy = dict(paper)
        paper_copy["_is_vlm"] = is_match
        paper_copy["_vlm_keywords"] = "; ".join(keywords) if keywords else ""
        annotated.append(paper_copy)

        if is_match:
            matched.append(paper_copy)

    return matched, annotated
