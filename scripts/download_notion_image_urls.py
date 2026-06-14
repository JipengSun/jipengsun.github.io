#!/usr/bin/env python3
"""Download Notion S3 images listed in a text file (one URL per line) into knowledge/assets/."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from notion_images import download_notion_image  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url_file", type=Path, help="text file with one presigned URL per line")
    parser.add_argument("--force", action="store_true", help="re-download even if cached")
    args = parser.parse_args()

    urls = [
        line.strip()
        for line in args.url_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    ok = fail = 0
    for url in urls:
        rel = download_notion_image(url, force=args.force)
        if rel and rel.startswith("../assets/"):
            ok += 1
            print(rel)
        else:
            fail += 1
            print(f"FAIL {url[:80]}...", file=sys.stderr)
    print(f"done: {ok} ok, {fail} failed", file=sys.stderr)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
