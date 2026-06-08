#!/usr/bin/env python3
"""Apply knowledge/raw/_in/*_fetch.json via mcp_notion_to_raw (writes knowledge/raw/{id}.txt)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP = ROOT / "scripts" / "mcp_notion_to_raw.py"
IN_DIR = ROOT / "knowledge" / "raw" / "_in"


def main() -> None:
    paths = sorted(IN_DIR.glob("*_fetch.json"))
    if not paths:
        print("no *_fetch.json under", IN_DIR, file=sys.stderr)
        sys.exit(1)
    for p in paths:
        subprocess.run([sys.executable, str(MCP), "--force", str(p)], check=True)


if __name__ == "__main__":
    main()
