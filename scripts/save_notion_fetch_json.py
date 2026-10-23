#!/usr/bin/env python3
"""Save a notion-fetch JSON object to knowledge/raw/_in/{id}.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "knowledge" / "raw" / "_in"

# Notion's newer fetch format, rewritten into the older one that notion_md_to_html.py reads.
_MENTION = re.compile(r'<mention url="(https://(?:www\.notion\.so/|app\.notion\.com/p/)[0-9a-f]{32})"\s*'
                      r'(?:/>|>.*?</mention>)')
_IMAGE = re.compile(r'<image source="notion-file-block://[^/"]+/([0-9a-f-]{36})\?space_id=([0-9a-f-]{36})'
                    r'&(?:amp;)?name=([^"&]+)"[^>]*?(?:/>|>.*?</image>)')
_INLINE_MATH = re.compile(r"(?<![\\$`])\$(?![$`\s])((?:\\\$|[^$\n])+?)(?<![\\\s])\$(?![$`\d])")


def classic_markdown(text: str) -> str:
    """$tex$ -> $`tex`$, <mention url> -> <mention-page url>, <image source> -> ![](S3 url), one line per block."""
    text = _MENTION.sub(r'<mention-page url="\1"/>', text)
    text = _IMAGE.sub(r"![](https://prod-files-secure.s3.us-west-2.amazonaws.com/\2/\1/\3)", text)
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if fenced or line.lstrip().startswith("```"):
            out.append(line)
            continue
        if not line.strip():
            continue  # blank lines only separate blocks, which the older format puts on their own lines
        out.append(_INLINE_MATH.sub(lambda m: "$`" + m.group(1) + "`$", line))
    return "\n".join(out)


def save(data: dict) -> str:
    IN_DIR.mkdir(parents=True, exist_ok=True)
    url = (data.get("url") or "").split("?", 1)[0]
    data["url"] = url
    if "<mention url=" in data.get("text", "") or "<image source=" in data.get("text", "") \
            or re.search(r"(?<![\\$`])\$(?![$`\s])", data.get("text", "")):
        data["text"] = classic_markdown(data["text"])
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
