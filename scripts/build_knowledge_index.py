#!/usr/bin/env python3
"""Regenerate the <ol class="ks-story-list"> block in knowledge-share.html.

Run after adding articles: python3 scripts/build_knowledge_index.py
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "knowledge-share.html"
ARTICLES = ROOT / "knowledge" / "articles"
SYNC_STATE = ROOT / "knowledge" / "raw" / "sync-state.json"

TOPIC: dict[str, tuple[str, str, str | None]] = {
    "self-attention": ("Machine Learning", "machine-learning", None),
    "vision-transformer-vit": ("Machine Learning", "machine-learning", None),
    "diffusion-transformer-dit": ("Machine Learning", "machine-learning", None),
    "classifier-free-guidance-cfg": ("Machine Learning", "machine-learning", None),
    "backpropagation": ("Machine Learning", "machine-learning", None),
    "autodiff": ("Machine Learning", "machine-learning", None),
    "kl-divergence": ("Machine Learning", "machine-learning", None),
    "elbo": ("Machine Learning", "machine-learning", None),
    "hilbert-transform": ("Math", "math", None),
    "graph-fourier-transform": ("Math", "math", None),
    "eigenvalue-decomposition": ("Math", "math", None),
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
    "pnp-with-diffusion": ("Computational Imaging", "computational-imaging", None),
    "generative-methods-for-deconv": ("Computational Imaging", "computational-imaging", None),
    "leaky-integrate-and-fire-lif": ("Neuromorphic Computing", "neuromorphic-computing", None),
    "hebbian-learning": ("Neuromorphic Computing", "neuromorphic-computing", None),
    "spike-timing-dependent-plasticity-stdp": ("Neuromorphic Computing", "neuromorphic-computing", None),
    "surrogate-gradient-learning": ("Neuromorphic Computing", "neuromorphic-computing", None),
    "angular-spectrum-method": ("Optics", "optics", None),
    "stokes-vectors": ("Optics", "optics", None),
    "diffraction-grating-formula": ("Optics", "optics", None),
    "orthographic-images-to-hologram": ("Optics", "optics", None),
}

DEK_OVERRIDE = {
    "camera-intrinsic-matrix": "Intrinsics K, focal length, principal point, and pixel skew.",
    "pnp-with-diffusion": "Plug-and-play priors with diffusion models for computational imaging inverse problems.",
    "mean-flow": "Notes on mean-flow generative modeling and its connection to flow matching.",
    "improved-mean-flow-imf": "Improved mean flow (iMF) — faster sampling and training for flow-based generative models.",
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


def load_slug_updated_at() -> dict[str, datetime]:
    """Map article slug → Notion content snapshot time from sync-state.json."""
    if not SYNC_STATE.is_file():
        return {}
    import json

    out: dict[str, datetime] = {}
    for rec in json.loads(SYNC_STATE.read_text(encoding="utf-8")).get("pages", {}).values():
        slug = rec.get("slug")
        raw = rec.get("notion_fetched_at") or rec.get("synced_at")
        if not slug or not raw:
            continue
        try:
            out[slug] = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
    return out


def ordered_slugs(updated_at: dict[str, datetime]) -> list[str]:
    """Newest Notion snapshot first; slugs without timestamps keep TOPIC dict order."""
    items: list[tuple[str, datetime | None, int]] = []
    for idx, slug in enumerate(TOPIC):
        if not (ARTICLES / f"{slug}.html").is_file():
            print(f"skip missing {slug}", file=sys.stderr)
            continue
        items.append((slug, updated_at.get(slug), idx))

    def sort_key(item: tuple[str, datetime | None, int]) -> tuple:
        slug, ts, idx = item
        if ts is not None:
            return (0, -ts.timestamp(), idx)
        return (1, idx, 0)

    items.sort(key=sort_key)
    return [slug for slug, _, _ in items]


def topic_counts() -> dict[str, tuple[str, int]]:
    """Map topic id → (display label, article count) for published articles."""
    counts: dict[str, tuple[str, int]] = {}
    for slug, (label, topic_id, _) in TOPIC.items():
        if not (ARTICLES / f"{slug}.html").is_file():
            continue
        if topic_id in counts:
            counts[topic_id] = (counts[topic_id][0], counts[topic_id][1] + 1)
        else:
            counts[topic_id] = (label, 1)
    return counts


def ordered_topics() -> list[tuple[str, str, int]]:
    """Topics sorted by article count (desc), then label (asc)."""
    items = [(tid, label, n) for tid, (label, n) in topic_counts().items()]
    items.sort(key=lambda x: (-x[2], x[1].lower()))
    return items


def render_topic_chips() -> str:
    chip = '\t\t\t\t\t\t\t\t<button type="button" class="ks-topic-chip{active}" data-ks-topic="{id}">{label}</button>'
    lines = [
        chip.format(id="all", label="All", active=" is-active"),
    ]
    for topic_id, label, _n in ordered_topics():
        lines.append(
            chip.format(
                id=html.escape(topic_id, quote=True),
                label=html.escape(label),
                active="",
            )
        )
    return "\n".join(lines) + "\n"


def render_stories() -> str:
    updated_at = load_slug_updated_at()
    lines: list[str] = []
    for slug in ordered_slugs(updated_at):
        kicker, topic_id, status = TOPIC[slug]
        title, dek = extract(slug)
        keywords = f"{title} {kicker} {slug.replace('-', ' ')}".lower()
        ts = updated_at.get(slug)
        updated_attr = (
            f' data-ks-updated="{html.escape(ts.isoformat(), quote=True)}"' if ts else ""
        )
        meta = (
            f'\n\t\t\t\t\t\t\t\t<div class="ks-story-meta"><span class="ks-tag">{status}</span></div>'
            if status
            else ""
        )
        lines.append(
            f'\t\t\t\t\t<li class="ks-story" data-ks-topic="{topic_id}"{updated_attr} '
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

    grid_m = re.search(
        r'(<div class="ks-topic-grid">)\s*.*?\s*(</div>)',
        text,
        re.S,
    )
    if not grid_m:
        sys.exit("ks-topic-grid not found in knowledge-share.html")
    topic_block = render_topic_chips()
    text = text[: grid_m.start(1)] + grid_m.group(1) + "\n" + topic_block + "\t\t\t\t\t\t\t" + grid_m.group(2) + text[grid_m.end(2) :]

    start = text.index('<ol class="ks-story-list"')
    start = text.index(">", start) + 1
    end = text.index("</ol>", start)
    new_block = render_stories()
    text = text[:start] + "\n" + new_block + text[end:]
    INDEX.write_text(text, encoding="utf-8")
    print(f"updated {INDEX.name}")


if __name__ == "__main__":
    main()
