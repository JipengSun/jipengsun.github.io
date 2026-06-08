#!/usr/bin/env python3
"""Stdin = page text body; args: page_id title — prints one notion-fetch JSON line to stdout."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    sys.exit(f"usage: {Path(sys.argv[0]).name} <32_hex_id> <title> < stdin (utf-8 text)")

pid, title = sys.argv[1], sys.argv[2]
if len(pid) != 32:
    sys.exit("id must be 32 hex chars")

text = sys.stdin.read()
d = {
    "metadata": {"type": "page"},
    "title": title,
    "url": f"https://www.notion.so/{pid}",
    "text": text,
}
sys.stdout.write(json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n")
