#!/usr/bin/env python3
"""
Generate word cloud image from keywords.json.
Outputs wordcloud/wordcloud.png (used directly in index.html).

Usage:
    python wordcloud/generate_image.py
"""

import json
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw

WORDCLOUD_DIR = Path(__file__).parent

# Topic → color mapping (matches index.html)
COLOR_MAP = [
    (["detection", "segmentation", "classification", "recognition"], "#6366f1"),
    (["sar", "radar", "insar", "polsar", "synthetic"],               "#3b82f6"),
    (["hyperspectral", "multispectral", "spectral", "unmixing"],     "#14b8a6"),
    (["uav", "drone", "aerial", "unmanned"],                         "#10b981"),
    (["vision", "language", "vlm", "multimodal", "foundation"],      "#a855f7"),
    (["change", "temporal", "monitoring", "dynamic"],                "#f59e0b"),
    (["domain", "transfer", "adaptation"],                           "#ec4899"),
    (["point cloud", "3d", "lidar", "depth"],                        "#06b6d4"),
    (["super resolution", "denoising", "restoration"],               "#f97316"),
    (["land", "urban", "vegetation", "crop", "flood"],               "#84cc16"),
]
FALLBACK = ["#6366f1", "#8b5cf6", "#ec4899", "#3b82f6", "#14b8a6", "#f59e0b", "#10b981"]
_fi = 0


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def color_of(word):
    global _fi
    w = word.lower()
    for keys, color in COLOR_MAP:
        if any(k in w for k in keys):
            return hex_to_rgb(color)
    c = FALLBACK[_fi % len(FALLBACK)]
    _fi += 1
    return hex_to_rgb(c)


def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    r, g, b = color_of(word)
    return f"rgb({r},{g},{b})"


def make_satellite_mask(width: int, height: int) -> np.ndarray:
    """Draw a satellite (cross) silhouette: wide horizontal panels + narrow vertical body."""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    cx, cy = width // 2, height // 2
    # Horizontal solar panels
    panel_w = int(width * 0.92)
    panel_h = int(height * 0.52)
    draw.rectangle(
        [cx - panel_w // 2, cy - panel_h // 2, cx + panel_w // 2, cy + panel_h // 2],
        fill="black",
    )
    # Vertical body
    body_w = int(width * 0.28)
    body_h = int(height * 0.88)
    draw.rectangle(
        [cx - body_w // 2, cy - body_h // 2, cx + body_w // 2, cy + body_h // 2],
        fill="black",
    )
    return np.array(img)


def generate(width=1400, height=600):
    from wordcloud import WordCloud

    kw_path = WORDCLOUD_DIR / "keywords.json"
    data = json.loads(kw_path.read_text(encoding="utf-8"))
    keywords = data["all"]["keywords"]

    # Build frequency dict (use weight as score)
    freq = {k["word"]: k["weight"] for k in keywords}

    mask = make_satellite_mask(width, height)

    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        mask=mask,
        color_func=color_func,
        max_words=80,
        prefer_horizontal=0.75,
        min_font_size=10,
        max_font_size=90,
        relative_scaling=0.55,
        collocations=False,
        margin=6,
        random_state=42,
    ).generate_from_frequencies(freq)

    out = WORDCLOUD_DIR / "wordcloud.png"
    wc.to_file(str(out))
    print(f"Saved → {out}  ({width}×{height})")


if __name__ == "__main__":
    generate()
