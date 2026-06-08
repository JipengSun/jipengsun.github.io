#!/usr/bin/env python3
"""Regenerate the <ol class="ks-story-list"> block in knowledge-share.html.

Run after adding articles: python3 scripts/build_knowledge_index.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "knowledge-share.html"
ARTICLES = ROOT / "knowledge" / "articles"

TOPIC: dict[str, tuple[str, str, str | None]] = {
    "self-attention": ("Machine Learning", "machine-learning", None),
    "vision-transformer-vit": ("Machine Learning", "machine-learning", None),
    "diffusion-transformer-dit": ("Machine Learning", "machine-learning", None),
    "classifier-free-guidance-cfg": ("Machine Learning", "machine-learning", None),
    "backpropagation": ("Machine Learning", "machine-learning", None),
    "autodiff": ("Machine Learning", "machine-learning", None),
    "kl-divergence": ("Machine Learning", "machine-learning", None),
    "elbo": ("Machine Learning", "machine-learning", None),
    "diffusion-model": ("Machine Learning", "machine-learning", None),
    "diffusion-from-sdes": ("Machine Learning", "machine-learning", None),
    "vae-vs-diffusion-elbo": ("Machine Learning", "machine-learning", None),
    "ddim": ("Machine Learning", "machine-learning", None),
    "ddpms-ddims-amp-score-based": ("Machine Learning", "machine-learning", None),
    "flow-matching": ("Machine Learning", "machine-learning", None),
    "mean-flow": ("Machine Learning", "machine-learning", None),
    "improved-mean-flow-imf": ("Machine Learning", "machine-learning", None),
    "optical-flow": ("Computer Vision", "computer-vision", None),
    "lucas-kanade-example": ("Computer Vision", "computer-vision", None),
    "raft": ("Computer Vision", "computer-vision", None),
    "camera-intrinsic-matrix": ("Computer Vision", "computer-vision", None),
    "camera-extrinsic-matrix": ("Computer Vision", "computer-vision", None),
    "colmap": ("Computer Vision", "computer-vision", None),
    "bundle-adjustment": ("Computer Vision", "computer-vision", "todo"),
    "proximal-algorithms": ("Optimization", "optimization", None),
    "neural-proximal-operators": ("Optimization", "optimization", None),
    "analytical-proximal-operators": ("Optimization", "optimization", None),
    "hqs": ("Optimization", "optimization", None),
    "admm": ("Optimization", "optimization", None),
    "lagrangian-method": ("Optimization", "optimization", None),
    "3d-gaussian-splatting": ("Computer Graphics", "computer-graphics", None),
    "nerf": ("Computer Graphics", "computer-graphics", None),
    "geometry-generation": ("Geometry Generation", "geometry-generation", "todo"),
    "pnp-with-diffusion": ("Computational Imaging", "computational-imaging", None),
    "generative-methods-for-deconv": ("Computational Imaging", "computational-imaging", None),
}

DEK_OVERRIDE = {
    "camera-intrinsic-matrix": "Intrinsics K, focal length, principal point, and pixel skew.",
    "pnp-with-diffusion": "Plug-and-play priors with diffusion models for computational imaging inverse problems.",
    "mean-flow": "Notes on mean-flow generative modeling and its connection to flow matching.",
    "improved-mean-flow-imf": "Improved mean flow (iMF) — faster sampling and training for flow-based generative models.",
    "geometry-generation": "3D shape synthesis, neural implicit surfaces, and mesh generation methods.",
}


def clean_title(t: str) -> str:
    t = re.sub(r"\*\*", "", t)
    return re.sub(r"\s*\(todo\)\s*", "", t, flags=re.I).strip()


def extract(slug: str) -> tuple[str, str]:
    text = (ARTICLES / f"{slug}.html").read_text(encoding="utf-8")
    title_m = re.search(r'<header><div class="title"><h2>([^<]+)', text) or re.search(
        r"<title>([^—<]+)", text
    )
    title = clean_title(title_m.group(1) if title_m else slug.replace("-", " ").title())
    if slug in DEK_OVERRIDE:
        return title, DEK_OVERRIDE[slug]
    body_m = re.search(r'<div class="kn-body">\s*(.*?)</div>', text, re.S)
    dek = ""
    if body_m:
        for p_m in re.finditer(r"<p>(.*?)</p>", body_m.group(1), re.S):
            raw = re.sub(r"<[^>]+>", "", p_m.group(1))
            raw = re.sub(r"\s+", " ", raw).strip()
            if len(raw) < 25 or raw.lower().startswith("notes on") or re.match(r"^\d+\.", raw):
                continue
            dek = raw
            break
    if not dek:
        dek = f"Study notes on {title.lower()}."
    if len(dek) > 155:
        dek = dek[:152].rsplit(" ", 1)[0] + "…"
    return title, dek


def render_stories() -> str:
    lines: list[str] = []
    for slug, (kicker, topic_id, status) in TOPIC.items():
        if not (ARTICLES / f"{slug}.html").is_file():
            print(f"skip missing {slug}", file=sys.stderr)
            continue
        title, dek = extract(slug)
        keywords = f"{title} {kicker} {slug.replace('-', ' ')}".lower()
        meta = (
            f'\n\t\t\t\t\t\t\t\t<div class="ks-story-meta"><span class="ks-tag">{status}</span></div>'
            if status
            else ""
        )
        lines.append(
            f'\t\t\t\t\t<li class="ks-story" data-ks-topic="{topic_id}" '
            f'data-ks-keywords="{html.escape(keywords, quote=True)}">\n'
            f'\t\t\t\t\t\t<a class="ks-story-link" href="knowledge/articles/{slug}.html">\n'
            f'\t\t\t\t\t\t\t<div class="ks-story-body">\n'
            f'\t\t\t\t\t\t\t\t<span class="ks-story-kicker">{html.escape(kicker)}</span>\n'
            f'\t\t\t\t\t\t\t\t<span class="ks-story-title">{html.escape(title)}</span>\n'
            f'\t\t\t\t\t\t\t\t<span class="ks-story-dek">{html.escape(dek)}</span>{meta}\n'
            f"\t\t\t\t\t\t\t</div>\n"
            f"\t\t\t\t\t\t</a>\n"
            f"\t\t\t\t\t</li>"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    text = INDEX.read_text(encoding="utf-8")
    start = text.index('<ol class="ks-story-list"')
    start = text.index(">", start) + 1
    end = text.index("</ol>", start)
    new_block = render_stories()
    INDEX.write_text(text[:start] + "\n" + new_block + text[end:], encoding="utf-8")
    print(f"updated {INDEX.name}")


if __name__ == "__main__":
    main()
