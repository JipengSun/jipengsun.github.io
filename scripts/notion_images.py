#!/usr/bin/env python3
"""Mirror Notion S3 image URLs into knowledge/assets/ for static hosting."""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "knowledge" / "assets"
ARTICLE_ASSET_PREFIX = "../assets"

NOTION_S3_IMAGE = re.compile(
    r"https://prod-files-secure\.s3[^/]*\.amazonaws\.com/[^/]+/([a-f0-9-]{36})/([^?\s)]+)",
    re.IGNORECASE,
)
IMG_MD = re.compile(r"!\[\]\(([^)]+)\)")


def parse_notion_image_url(url: str) -> tuple[str, str] | None:
    m = NOTION_S3_IMAGE.search(url)
    if not m:
        return None
    return m.group(1).lower(), m.group(2)


def asset_filename(asset_id: str, remote_name: str) -> str:
    ext = Path(remote_name).suffix.lower() or ".png"
    return f"{asset_id}{ext}"


def asset_relpath(asset_id: str, remote_name: str) -> str:
    return f"{ARTICLE_ASSET_PREFIX}/{asset_filename(asset_id, remote_name)}"


def download_notion_image(url: str, *, force: bool = False) -> str | None:
    """Download image; return path relative to knowledge/articles/."""
    if url.startswith(ARTICLE_ASSET_PREFIX + "/"):
        return url

    parsed = parse_notion_image_url(url)
    if not parsed:
        return None

    asset_id, remote_name = parsed
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    dest = ASSETS_DIR / asset_filename(asset_id, remote_name)
    rel = asset_relpath(asset_id, remote_name)

    if dest.is_file() and not force:
        return rel

    req = urllib.request.Request(url, headers={"User-Agent": "jipengsun.github.io-knowledge-sync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
        return rel
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if dest.is_file():
            print(f"warn: download failed, using cached {dest.name}: {exc}", file=sys.stderr)
            return rel
        print(f"warn: download failed for {asset_id}: {exc}", file=sys.stderr)
        return None


def mirror_images_in_markdown(md: str, *, force: bool = False) -> tuple[str, int]:
    """Replace Notion image URLs with local asset paths. Returns (md, count mirrored)."""
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        url = m.group(1).strip()
        local = download_notion_image(url, force=force)
        if local and local != url:
            count += 1
            return f"![]({local})"
        if local:
            return f"![]({local})"
        return m.group(0)

    return IMG_MD.sub(repl, md), count


def find_remote_image_urls(text: str) -> list[str]:
    urls: list[str] = []
    for m in IMG_MD.finditer(text):
        url = m.group(1).strip()
        if parse_notion_image_url(url):
            urls.append(url)
    return urls
