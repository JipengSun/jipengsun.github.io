#!/usr/bin/env python3
"""Inject SEO metadata into pages and generate sitemap.xml + robots.txt.

Adds, idempotently (between <!-- seo:auto:start --> / <!-- seo:auto:end -->):
  - <meta name="description">, author, robots
  - <link rel="canonical">
  - Open Graph + Twitter card tags
  - JSON-LD structured data (Article / Person) tying content to "Jipeng Sun"

Then writes a sitemap.xml (with lastmod from Notion sync state) and robots.txt so
Google can discover and rank every Knowledge Share article.

Run standalone:  python3 scripts/seo.py
Also invoked automatically at the end of scripts/build_knowledge_index.py.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "knowledge" / "articles"
INDEX = ROOT / "knowledge-share.html"
HOME = ROOT / "index.html"
BLOG = ROOT / "blog"
SYNC_STATE = ROOT / "knowledge" / "raw" / "sync-state.json"

# A page with less body text than this is an overview stub — still crawlable and still
# linked from knowledge-share.html, but not worth asking Google to index, since thin
# pages come back as "crawled, currently not indexed" and drag down the whole section.
MIN_SITEMAP_BODY_CHARS = 250

BASE_URL = "https://jipengsun.github.io"
AUTHOR = "Jipeng Sun"

SEO_START = "<!-- seo:auto:start -->"
SEO_END = "<!-- seo:auto:end -->"


def clean_title(raw: str) -> str:
    t = html.unescape(raw).replace("**", "")
    t = re.split(r"\s+—\s+", t)[0]
    t = re.sub(r"\s*\(todo\)\s*", "", t, flags=re.I)
    return t.strip()


def strip_math_and_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def derive_description(html_text: str, fallback_title: str) -> str:
    body_m = re.search(r'<div class="kn-body">\s*(.*?)</div>\s*</article>', html_text, re.S)
    body = body_m.group(1) if body_m else html_text
    for p_m in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.S):
        raw = strip_math_and_tags(p_m.group(1))
        if len(raw) < 40 or re.match(r"^\d+\.", raw):
            continue
        return _truncate(raw)
    return f"Study notes by {AUTHOR} on {fallback_title.lower()}."


def _truncate(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def load_slug_lastmod() -> dict[str, str]:
    if not SYNC_STATE.is_file():
        return {}
    out: dict[str, str] = {}
    data = json.loads(SYNC_STATE.read_text(encoding="utf-8"))
    for rec in data.get("pages", {}).values():
        slug = rec.get("slug")
        raw = rec.get("notion_fetched_at") or rec.get("synced_at")
        if not slug or not raw:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        out[slug] = dt.date().isoformat()
    return out


def _meta(name: str, content: str, *, prop: bool = False) -> str:
    key = "property" if prop else "name"
    return f'<meta {key}="{name}" content="{html.escape(content, quote=True)}" />'


def render_seo_block(
    *,
    indent: str,
    title: str,
    description: str,
    canonical: str,
    og_type: str,
    jsonld: dict,
    site_name: str = f"{AUTHOR} — Knowledge Share",
) -> str:
    esc_title = html.escape(title, quote=True)
    lines = [
        SEO_START,
        _meta("description", description),
        _meta("author", AUTHOR),
        _meta("robots", "index, follow"),
        f'<link rel="canonical" href="{html.escape(canonical, quote=True)}" />',
        _meta("og:type", og_type, prop=True),
        _meta("og:site_name", site_name, prop=True),
        _meta("og:title", title, prop=True),
        _meta("og:description", description, prop=True),
        _meta("og:url", canonical, prop=True),
        _meta("twitter:card", "summary"),
        _meta("twitter:title", title),
        _meta("twitter:description", description),
        '<script type="application/ld+json">'
        + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
        + "</script>",
        SEO_END,
    ]
    _ = esc_title
    return ("\n" + indent).join(lines)


def inject_block(html_text: str, block: str) -> str:
    # Consume the block's own indentation too. Without the leading [ \t]*, every run
    # left the old indent behind and the next line drifted two tabs further right.
    existing = re.compile(
        r"[ \t]*" + re.escape(SEO_START) + r".*?" + re.escape(SEO_END) + r"[ \t]*\n?",
        re.S,
    )
    html_text = existing.sub("", html_text)
    # Drop hand-written description tags so the generated block is the only one; two
    # competing <meta name="description"> tags leave Google to pick arbitrarily.
    html_text = re.sub(
        r"[ \t]*<meta\s+name=[\"']description[\"'][^>]*>[ \t]*\n?", "", html_text, flags=re.I
    )
    m = re.search(r"(?P<indent>[ \t]*)<title>.*?</title>", html_text, re.S)
    if not m:
        raise ValueError("no <title> found")
    indent = m.group("indent")
    insert_at = m.end()
    rest = html_text[insert_at:]
    # Re-indent the line the block is inserted above, so runs from before the fix above
    # (which left their indentation behind) get normalized instead of staying drifted.
    rest = re.sub(r"^\n[ \t]*", "\n" + indent, rest, count=1)
    return html_text[:insert_at] + "\n" + indent + block + rest


def article_jsonld(title: str, description: str, canonical: str, lastmod: str | None) -> dict:
    data: dict = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": canonical,
        "mainEntityOfPage": canonical,
        "inLanguage": "en",
        "author": {"@type": "Person", "name": AUTHOR, "url": BASE_URL + "/"},
        "publisher": {"@type": "Person", "name": AUTHOR, "url": BASE_URL + "/"},
        "isPartOf": {
            "@type": "Blog",
            "name": f"{AUTHOR} — Knowledge Share",
            "url": BASE_URL + "/knowledge-share.html",
        },
    }
    if lastmod:
        data["dateModified"] = lastmod
    return data


def process_article(path: Path, lastmod: str | None) -> None:
    text = path.read_text(encoding="utf-8")
    title_m = re.search(r"<title>(.*?)</title>", text, re.S)
    title = clean_title(title_m.group(1) if title_m else path.stem.replace("-", " ").title())
    description = derive_description(text, title)
    canonical = f"{BASE_URL}/knowledge/articles/{path.name}"
    block = render_seo_block(
        indent="\t",
        title=title,
        description=description,
        canonical=canonical,
        og_type="article",
        jsonld=article_jsonld(title, description, canonical, lastmod),
    )
    path.write_text(inject_block(text, block), encoding="utf-8")


def process_page(
    path: Path,
    *,
    canonical: str,
    description: str,
    jsonld: dict,
    indent: str,
    site_name: str = f"{AUTHOR} — Knowledge Share",
) -> None:
    text = path.read_text(encoding="utf-8")
    title_m = re.search(r"<title>(.*?)</title>", text, re.S)
    title = html.unescape((title_m.group(1) if title_m else AUTHOR)).strip()
    block = render_seo_block(
        indent=indent,
        title=title,
        description=description,
        canonical=canonical,
        og_type="website",
        jsonld=jsonld,
        site_name=site_name,
    )
    path.write_text(inject_block(text, block), encoding="utf-8")


def person_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": AUTHOR,
        "url": BASE_URL + "/",
        "jobTitle": "PhD Researcher",
        "knowsAbout": [
            "Computational Imaging",
            "Optics",
            "Machine Learning",
            "Computer Vision",
        ],
        "sameAs": [BASE_URL + "/knowledge-share.html"],
    }


def body_text_length(html_text: str) -> int:
    m = re.search(r'<div class="kn-body".*?>(.*)', html_text, re.S)
    body = m.group(1) if m else html_text
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S)
    return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip())


def blog_post_paths() -> list[Path]:
    """Restored Jekyll-era posts, at blog/YYYY/MM/DD/slug.html."""
    return sorted(BLOG.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/*.html"))


def sitemap_entries() -> list[tuple[str, str | None]]:
    today = datetime.now(timezone.utc).date().isoformat()
    lastmod = load_slug_lastmod()
    entries: list[tuple[str, str | None]] = [
        (BASE_URL + "/", today),
        (BASE_URL + "/research.html", today),
        (BASE_URL + "/projects.html", today),
        (BASE_URL + "/single.html", today),
        (BASE_URL + "/knowledge-share.html", today),
        (BASE_URL + "/blog/index.html", today),
    ]
    for path in sorted(ARTICLES.glob("*.html")):
        if body_text_length(path.read_text(encoding="utf-8")) < MIN_SITEMAP_BODY_CHARS:
            continue
        canonical = f"{BASE_URL}/knowledge/articles/{path.name}"
        mod = lastmod.get(path.stem)
        if not mod:
            mod = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date().isoformat()
        entries.append((canonical, mod))

    for path in blog_post_paths():
        # Canonicals use the extensionless URL Google already has indexed.
        rel = path.relative_to(ROOT).with_suffix("").as_posix()
        entries.append((f"{BASE_URL}/{rel}", "-".join(path.parts[-4:-1])))
    return entries


def build_sitemap() -> Path:
    rows = []
    for loc, mod in sitemap_entries():
        row = f"\t<url>\n\t\t<loc>{html.escape(loc, quote=True)}</loc>"
        if mod:
            row += f"\n\t\t<lastmod>{mod}</lastmod>"
        row += "\n\t</url>"
        rows.append(row)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )
    out = ROOT / "sitemap.xml"
    out.write_text(xml, encoding="utf-8")
    return out


def write_robots() -> Path:
    out = ROOT / "robots.txt"
    out.write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + BASE_URL + "/sitemap.xml\n",
        encoding="utf-8",
    )
    return out


def run() -> None:
    lastmod = load_slug_lastmod()
    n = 0
    for path in sorted(ARTICLES.glob("*.html")):
        process_article(path, lastmod.get(path.stem))
        n += 1

    if INDEX.is_file():
        process_page(
            INDEX,
            canonical=BASE_URL + "/knowledge-share.html",
            description=(
                f"Study notes by {AUTHOR} on machine learning, computer vision, optics, "
                "computational imaging, optimization, and math."
            ),
            jsonld={
                "@context": "https://schema.org",
                "@type": "Blog",
                "name": f"{AUTHOR} — Knowledge Share",
                "url": BASE_URL + "/knowledge-share.html",
                "author": {"@type": "Person", "name": AUTHOR, "url": BASE_URL + "/"},
            },
            indent="\t\t",
        )

    # Hand-maintained pages that previously carried no canonical and no description.
    standalone = [
        (
            "research.html",
            "Peer-reviewed publications and ongoing research by Jipeng Sun in computational "
            "imaging, optics, and machine learning.",
        ),
        (
            "projects.html",
            f"Selected projects by {AUTHOR} across computational imaging, optics, and "
            "machine learning.",
        ),
        (
            "single.html",
            f"Why {AUTHOR} works on computational imaging: grounding flat optics and the case "
            "for a PhD in the field.",
        ),
    ]
    for name, description in standalone:
        path = ROOT / name
        if not path.is_file():
            continue
        canonical = f"{BASE_URL}/{name}"
        process_page(
            path,
            canonical=canonical,
            description=description,
            jsonld={
                "@context": "https://schema.org",
                "@type": "WebPage",
                "url": canonical,
                "inLanguage": "en",
                "author": {"@type": "Person", "name": AUTHOR, "url": BASE_URL + "/"},
                "isPartOf": {"@type": "WebSite", "name": AUTHOR, "url": BASE_URL + "/"},
            },
            indent="\t\t",
            site_name=AUTHOR,
        )

    if HOME.is_file():
        process_page(
            HOME,
            canonical=BASE_URL + "/",
            description=(
                f"{AUTHOR} is a PhD researcher in computational imaging, optics, and machine "
                "learning. Research, projects, and study notes."
            ),
            jsonld=person_jsonld(),
            indent="\t\t",
            site_name=AUTHOR,
        )

    sitemap = build_sitemap()
    robots = write_robots()
    print(f"seo: updated {n} articles + index/home; wrote {sitemap.name}, {robots.name}")


if __name__ == "__main__":
    run()
