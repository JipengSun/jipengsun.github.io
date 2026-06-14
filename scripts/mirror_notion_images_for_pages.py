#!/usr/bin/env python3
"""Download Notion images from raw exports and rebuild article HTML with local asset paths."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "knowledge" / "raw"
sys.path.insert(0, str(ROOT / "scripts"))

from notion_images import find_remote_image_urls, mirror_images_in_markdown, download_notion_image  # noqa: E402
from notion_md_to_html import NOTION_TO_SLUG, build_full_page, extract_from_mcp_view, notion_body_to_html  # noqa: E402

IMAGE_PAGE_IDS = [
    "31701d9f5287804d82e1fa6fb1a684f7",
    "33601d9f5287804f95a7fed3efafb131",
    "33901d9f52878061b15ce12ba00b5a33",
    "35501d9f528780dabe98fe56ccb15d78",
    "35501d9f5287801e9a5ce5862e81f512",
    "33b01d9f5287806f9ce5f06def87d02a",
    "33b01d9f52878094a2f1d26eeebe0983",
    "34901d9f528780b8a125f62ee430ac4d",
]


def main() -> None:
    # Download from current raw URLs (must be fresh presigned URLs).
    seen: set[str] = set()
    for pid in IMAGE_PAGE_IDS:
        raw_path = RAW / f"{pid}.txt"
        if not raw_path.is_file():
            print(f"skip missing raw {pid}", file=sys.stderr)
            continue
        _, body = extract_from_mcp_view(raw_path.read_text(encoding="utf-8"))
        for url in find_remote_image_urls(body):
            if url in seen:
                continue
            seen.add(url)
            rel = download_notion_image(url, force=True)
            if not rel:
                print(f"FAIL download {url[:70]}...", file=sys.stderr)

    # Rebuild HTML (uses cached assets when presigned URLs expire).
    for pid in IMAGE_PAGE_IDS:
        slug = NOTION_TO_SLUG[pid]
        raw = (RAW / f"{pid}.txt").read_text(encoding="utf-8")
        title, body = extract_from_mcp_view(raw)
        body, n_img = mirror_images_in_markdown(body)
        inner = notion_body_to_html(body)
        html = build_full_page(title, "\t\t\t\t" + inner.replace("\n", "\n\t\t\t\t"), slug)
        (ROOT / "knowledge" / "articles" / f"{slug}.html").write_text(html, encoding="utf-8")
        print(f"{slug}: {n_img} local images")


if __name__ == "__main__":
    main()
