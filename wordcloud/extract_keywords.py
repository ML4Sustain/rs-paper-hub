#!/usr/bin/env python3
"""
Extract keywords from RS paper titles/abstracts using KeyBERT (BERT-based).
Saves results to wordcloud/keywords.json, grouped by data source.

Usage:
    python wordcloud/extract_keywords.py
    python wordcloud/extract_keywords.py --source sar   # single source
    python wordcloud/extract_keywords.py --top 100      # top N keywords
"""

import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import json
import os
import re
import argparse
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "output"
WORDCLOUD_DIR = Path(__file__).parent
STOPWORDS_FILE = WORDCLOUD_DIR / "stopwords_rs.txt"

# Data sources to process
DATA_SOURCES = {
    "all":   "papers.json",
    "vlm":   "papers_vlm.json",
    "uav":   "papers_uav.json",
    "agent": "papers_agent.json",
    "sar":   "papers_sar.json",
    "hyp":   "papers_hyp.json",
}

MODEL_NAME = "all-MiniLM-L6-v2"


def load_stopwords() -> set[str]:
    stopwords = set()
    with open(STOPWORDS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                stopwords.add(line.lower())
    # Use NLTK stopwords only if already cached locally (no network)
    try:
        import nltk
        from nltk.corpus import stopwords as nltk_sw
        stopwords |= set(nltk_sw.words("english"))
    except Exception:
        # Fallback: common English stopwords
        stopwords |= {
            "i","me","my","myself","we","our","ours","ourselves","you","your",
            "yours","yourself","yourselves","he","him","his","himself","she","her",
            "hers","herself","it","its","itself","they","them","their","theirs",
            "themselves","what","which","who","whom","this","that","these","those",
            "am","is","are","was","were","be","been","being","have","has","had",
            "having","do","does","did","doing","a","an","the","and","but","if",
            "or","because","as","until","while","of","at","by","for","with",
            "about","against","between","into","through","during","before","after",
            "above","below","to","from","up","down","in","out","on","off","over",
            "under","again","further","then","once","here","there","when","where",
            "why","how","all","both","each","few","more","most","other","some",
            "such","no","nor","not","only","own","same","so","than","too","very",
            "s","t","can","will","just","don","should","now","d","ll","m","o",
            "re","ve","y","ain","aren","couldn","didn","doesn","hadn","hasn",
            "haven","isn","ma","mightn","mustn","needn","shan","shouldn","wasn",
            "weren","won","wouldn",
        }
    return stopwords


def clean_text(title: str, abstract: str) -> str:
    text = f"{title}. {abstract}"
    # Remove URLs
    text = re.sub(r"https?://\S+", " ", text)
    # Remove special chars, keep hyphens in compound words
    text = re.sub(r"[^\w\s\-]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords_keybert(texts: list[str], stopwords: set[str], top_n: int = 200) -> list[tuple[str, float]]:
    from keybert import KeyBERT

    print(f"  Loading model: {MODEL_NAME} ...")
    kw_model = KeyBERT(MODEL_NAME)

    # KeyBERT on concatenated corpus (batch for speed)
    # We extract from individual titles first, then aggregate by frequency × score
    kw_counter: dict[str, list[float]] = {}

    batch_size = 256
    total = len(texts)
    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        if i % 1000 == 0:
            print(f"  Processing {i}/{total}...")
        results = kw_model.extract_keywords(
            batch,
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=8,
            use_mmr=True,
            diversity=0.5,
        )
        # results is list of list of (kw, score)
        for doc_kws in results:
            for kw, score in doc_kws:
                kw_clean = kw.lower().strip()
                # Filter stopwords and very short tokens
                if kw_clean in stopwords:
                    continue
                if len(kw_clean) < 3:
                    continue
                # Filter if all tokens are stopwords
                tokens = kw_clean.split()
                if all(tok in stopwords for tok in tokens):
                    continue
                kw_counter.setdefault(kw_clean, []).append(score)

    # Aggregate: frequency × mean_score
    aggregated = []
    for kw, scores in kw_counter.items():
        freq = len(scores)
        mean_score = sum(scores) / freq
        weight = freq * mean_score
        aggregated.append((kw, freq, round(mean_score, 4), round(weight, 4)))

    # Sort by weight descending
    aggregated.sort(key=lambda x: -x[3])
    return aggregated[:top_n]


def process_source(key: str, filename: str, stopwords: set[str], top_n: int) -> dict:
    path = OUTPUT_DIR / filename
    if not path.exists():
        print(f"  [{key}] File not found: {path}, skipped")
        return {}

    with open(path, encoding="utf-8") as f:
        papers = json.load(f)
    print(f"\n[{key}] {len(papers)} papers → extracting keywords...")

    texts = [clean_text(str(p.get("Title", "")), str(p.get("Abstract", ""))) for p in papers]
    keywords = extract_keywords_keybert(texts, stopwords, top_n=top_n)

    return {
        "source": key,
        "paper_count": len(papers),
        "keywords": [
            {"word": kw, "freq": freq, "bert_score": score, "weight": weight}
            for kw, freq, score, weight in keywords
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default=None, help="Single source key (e.g. sar)")
    parser.add_argument("--top", type=int, default=200, help="Top N keywords per source")
    args = parser.parse_args()

    print("Loading stopwords...")
    stopwords = load_stopwords()
    print(f"  {len(stopwords)} stopwords loaded")

    sources = {args.source: DATA_SOURCES[args.source]} if args.source else DATA_SOURCES
    results = {}

    for key, filename in sources.items():
        result = process_source(key, filename, stopwords, args.top)
        if result:
            results[key] = result

    from datetime import date
    results["_last_updated"] = date.today().isoformat()

    out_path = WORDCLOUD_DIR / "keywords.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved → {out_path}")
    for key, r in results.items():
        print(f"  [{key}] {r['paper_count']} papers → {len(r['keywords'])} keywords")


if __name__ == "__main__":
    main()
