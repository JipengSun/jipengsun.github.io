#!/usr/bin/env python3
"""Force-sync knowledge/raw/*.txt from _in JSON exports, then rebuild articles + index.

Prefer incremental sync:
  python3 scripts/update_knowledge_from_notion.py plan
  python3 scripts/update_knowledge_from_notion.py sync < fetch.json
  python3 scripts/update_knowledge_from_notion.py apply

This script remains as a full refresh (applies all _in exports with --force).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATE = ROOT / "scripts" / "update_knowledge_from_notion.py"


def main() -> None:
    subprocess.run([sys.executable, str(UPDATE), "apply", "--force"], check=True)


if __name__ == "__main__":
    main()
