#!/usr/bin/env python3
"""Save a notion-fetch JSON object to knowledge/raw/_in/{id}.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "knowledge" / "raw" / "_in"


def save(data: dict) -> str:
    IN_DIR.mkdir(parents=True, exist_ok=True)
    url = data.get("url") or ""
    pid = url.rsplit("/", 1)[-1]
    if len(pid) != 32:
        raise SystemExit(f"bad url: {url!r}")
    out = IN_DIR / f"{pid}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return pid


def main() -> None:
    if len(sys.argv) > 1:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    else:
        data = json.load(sys.stdin)
    print(save(data))


if __name__ == "__main__":
    main()
