#!/usr/bin/env python3
"""Read one notion-fetch JSON line from a UTF-8 file; write _in/{id}_fetch.json and raw .txt."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP = ROOT / "scripts" / "mcp_notion_to_raw.py"
IN_DIR = ROOT / "knowledge" / "raw" / "_in"


def main() -> None:
    src = Path(sys.argv[1])
    line = src.read_text(encoding="utf-8").strip()
    d = json.loads(line)
    pid = (d.get("url") or "").rsplit("/", 1)[-1]
    if len(pid) != 32:
        sys.exit(f"bad url in json: {d.get('url')!r}")
    IN_DIR.mkdir(parents=True, exist_ok=True)
    out = IN_DIR / f"{pid}_fetch.json"
    out.write_text(line + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(MCP), str(out)], check=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"usage: {Path(sys.argv[0]).name} <one-line-json-file>")
    main()
