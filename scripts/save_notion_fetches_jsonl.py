#!/usr/bin/env python3
"""Save notion-fetch JSON objects from a JSONL file into knowledge/raw/_in/."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from save_notion_fetch_json import save  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()
    for line in args.jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        print(save(json.loads(line)))


if __name__ == "__main__":
    main()
