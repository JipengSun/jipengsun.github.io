#!/usr/bin/env python3
"""Render _posts/*.md into static HTML at the original Jekyll permalink paths.

Adding .nojekyll (commit 00a8d69) stopped GitHub Pages from building _posts/, so every
URL matching the old `permalink: /blog/:year/:month/:day/:title` pattern started
returning 404 — including pages Google had already indexed. This script rebuilds them
as plain static files so those URLs resolve again, with the original post content.

GitHub Pages serves `foo.html` at the extensionless `/foo`, so writing
`blog/2022/11/12/DDPM.html` restores `https://jipengsun.github.io/blog/2022/11/12/DDPM`
— the exact URL in Google's index. Canonicals point at the extensionless form.

Also regenerates blog/index.html as an archive index linking every post.

Run:  python3 scripts/build_blog_archive.py
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "_posts"
BLOG = ROOT / "blog"

BASE_URL = "https://jipengsun.github.io"
AUTHOR = "Jipeng Sun"
GA_ID = "G-LCC4R0HD24"

POST_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$")
FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
# Matches both <https://…> autolinks and bare URLs. Applied before HTML-escaping so
# that query strings containing & survive intact.
URL_RE = re.compile(r"<(https?://[^\s>]+)>|(?<![\w\"'=])(https?://[^\s<>\"']+)")
# Null bytes cannot occur in the source markdown, so they are safe placeholders.
LINK_TOKEN = "\x00link{}\x00"


# --------------------------------------------------------------------------- parsing


class Post:
    def __init__(self, path: Path) -> None:
        self.path = path
        m = POST_RE.match(path.stem)
        if not m:
            raise ValueError(f"unexpected post filename: {path.name}")
        self.year, self.month, self.day, self.slug = m.groups()
        self.date = date(int(self.year), int(self.month), int(self.day))

        text = path.read_text(encoding="utf-8")
        fm_m = FRONT_MATTER_RE.match(text)
        front_matter = fm_m.group(1) if fm_m else ""
        self.body = text[fm_m.end():] if fm_m else text
        self.had_front_matter = bool(fm_m)

        self.title = self._title(front_matter)

    def _title(self, front_matter: str) -> str:
        m = re.search(r"^title:\s*(.+)$", front_matter, re.M)
        if m:
            return m.group(1).strip().strip('"').strip("'")
        # Posts without front matter lead with their title as a heading.
        m = re.search(r"^#{1,6}\s+(.+)$", self.body, re.M)
        if m:
            return m.group(1).strip()
        return self.slug.replace("-", " ").replace("_", " ").strip()

    @property
    def url_path(self) -> str:
        return f"/blog/{self.year}/{self.month}/{self.day}/{self.slug}"

    @property
    def out_path(self) -> Path:
        return BLOG / self.year / self.month / self.day / f"{self.slug}.html"

    @property
    def canonical(self) -> str:
        return BASE_URL + self.url_path


def load_posts() -> list[Post]:
    return sorted(
        (Post(p) for p in POSTS.glob("*.md")),
        key=lambda p: (p.date, p.slug),
        reverse=True,
    )


# ------------------------------------------------------------------------ markdown


def inline(text: str) -> str:
    # Pull URLs out first: escaping them would mangle & in query strings, and the
    # emphasis passes below would otherwise chew on underscores inside them.
    urls: list[str] = []

    def stash(m: re.Match[str]) -> str:
        # Delimited <…> autolinks are already unambiguous; bare URLs need trailing
        # sentence punctuation trimmed off.
        urls.append(m.group(1) or m.group(2).rstrip(".,;:)"))
        return LINK_TOKEN.format(len(urls) - 1)

    out = URL_RE.sub(stash, text)
    out = html.escape(out)
    out = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    # Notion-style escaped asterisks left over from the original notes.
    out = out.replace("\\*", "*")

    for idx, url in enumerate(urls):
        safe = html.escape(url, quote=True)
        anchor = f'<a href="{safe}" rel="noopener">{html.escape(url)}</a>'
        out = out.replace(LINK_TOKEN.format(idx), anchor)
    return out


def markdown_to_html(md: str) -> str:
    blocks: list[str] = []
    para: list[str] = []
    lines = md.replace("\r\n", "\n").split("\n")
    i = 0

    def flush() -> None:
        if para:
            blocks.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush()
            i += 1
            continue
        if line == "---":
            flush()
            blocks.append("<hr />")
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush()
            # The page <h1> is the post title, so in-body headings start at <h2>.
            level = min(max(len(heading.group(1)), 2), 6)
            blocks.append(f"<h{level}>{inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append("<li>" + inline(re.sub(r"^[-*]\s+", "", lines[i].strip())) + "</li>")
                i += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append("<li>" + inline(re.sub(r"^\d+\.\s+", "", lines[i].strip())) + "</li>")
                i += 1
            blocks.append("<ol>" + "".join(items) + "</ol>")
            continue
        para.append(line)
        i += 1

    flush()
    return "\n".join(blocks)


def derive_description(md: str, title: str) -> str:
    for raw in re.split(r"\n\s*\n", md):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("<http"):
            continue
        plain = re.sub(r"<[^>]+>", " ", line)
        plain = re.sub(r"[*\\]", "", plain)
        plain = re.sub(r"\s+", " ", plain).strip()
        if len(plain) < 60:
            continue
        if len(plain) <= 160:
            return plain
        return plain[:159].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
    return f"Research note by {AUTHOR} on {title}."


# -------------------------------------------------------------------------- render


def chrome(prefix: str, *, active: str) -> tuple[str, str]:
    """Return (header, menu) markup with links resolved against `prefix`."""

    def cls(name: str) -> str:
        return ' class="active"' if name == active else ""

    header = f"""\t\t<header id="header">
\t\t\t<p class="site-title"><a href="{prefix}index.html">Jipeng Sun</a></p>
\t\t\t<nav class="links">
\t\t\t\t<ul>
\t\t\t\t\t<li{cls("home")}><a href="{prefix}index.html">Home</a></li>
\t\t\t\t\t<li{cls("research")}><a href="{prefix}research.html">Research</a></li>
\t\t\t\t\t<li{cls("knowledge")}><a href="{prefix}knowledge-share.html">Knowledge Share</a></li>
\t\t\t\t\t<li><a href="https://sites.northwestern.edu/cs396vrsystems/" data-ga-event="vr_ar_course">VR/AR Course</a></li>
\t\t\t\t</ul>
\t\t\t</nav>
\t\t\t<nav class="main">
\t\t\t\t<ul>
\t\t\t\t\t<li class="menu"><a class="fa-bars" href="#menu">Menu</a></li>
\t\t\t\t</ul>
\t\t\t</nav>
\t\t</header>"""

    menu = f"""\t\t<section id="menu">
\t\t\t<section>
\t\t\t\t<ul class="links">
\t\t\t\t\t<li><a href="{prefix}index.html"><h3>Home</h3><p>Jipeng Sun's Homepage</p></a></li>
\t\t\t\t\t<li><a href="{prefix}research.html"><h3>Research</h3><p>Publications &amp; Papers</p></a></li>
\t\t\t\t\t<li><a href="{prefix}knowledge-share.html"><h3>Knowledge Share</h3><p>Study notes</p></a></li>
\t\t\t\t\t<li><a href="{prefix}blog/index.html"><h3>Paper Notes Archive</h3><p>2022 paper reviews</p></a></li>
\t\t\t\t</ul>
\t\t\t</section>
\t\t</section>"""
    return header, menu


def seo_block(*, title: str, description: str, canonical: str, jsonld: dict) -> str:
    def meta(name: str, content: str, *, prop: bool = False) -> str:
        key = "property" if prop else "name"
        return f'\t<meta {key}="{name}" content="{html.escape(content, quote=True)}" />'

    return "\n".join(
        [
            "\t<!-- seo:auto:start -->",
            meta("description", description),
            meta("author", AUTHOR),
            meta("robots", "index, follow"),
            f'\t<link rel="canonical" href="{html.escape(canonical, quote=True)}" />',
            meta("og:type", "article", prop=True),
            meta("og:site_name", f"{AUTHOR} — Paper Notes", prop=True),
            meta("og:title", title, prop=True),
            meta("og:description", description, prop=True),
            meta("og:url", canonical, prop=True),
            meta("twitter:card", "summary"),
            meta("twitter:title", title),
            meta("twitter:description", description),
            '\t<script type="application/ld+json">'
            + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
            + "</script>",
            "\t<!-- seo:auto:end -->",
        ]
    )


def ga_snippet(prefix: str) -> str:
    return f"""\t<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
\t<script>
\t  window.dataLayer = window.dataLayer || [];
\t  function gtag(){{dataLayer.push(arguments);}}
\t  gtag('js', new Date());
\t  gtag('config', '{GA_ID}');
\t</script>
\t<script src="{prefix}assets/js/ga-events.js"></script>"""


def scripts(prefix: str) -> str:
    return "\n".join(
        f'\t<script src="{prefix}assets/js/{name}"></script>'
        for name in ("jquery.min.js", "browser.min.js", "breakpoints.min.js", "util.js", "main.js")
    )


def render_post(post: Post, related: list[Post]) -> str:
    prefix = "../../../../"
    description = derive_description(post.body, post.title)
    body_html = markdown_to_html(post.body)
    header, menu = chrome(prefix, active="")
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.title,
        "description": description,
        "url": post.canonical,
        "mainEntityOfPage": post.canonical,
        "inLanguage": "en",
        "datePublished": post.date.isoformat(),
        "dateModified": post.date.isoformat(),
        "author": {"@type": "Person", "name": AUTHOR, "url": BASE_URL + "/"},
        "publisher": {"@type": "Person", "name": AUTHOR, "url": BASE_URL + "/"},
        "isPartOf": {
            "@type": "Blog",
            "name": f"{AUTHOR} — Paper Notes",
            "url": BASE_URL + "/blog/index.html",
        },
    }

    related_html = ""
    if related:
        items = "".join(
            f'<li><a href="{prefix}blog/{r.year}/{r.month}/{r.day}/{r.slug}.html">'
            f"{html.escape(r.title)}</a></li>"
            for r in related
        )
        related_html = (
            '\n\t\t\t\t<aside class="kn-related">\n'
            "\t\t\t\t\t<h2>More paper notes</h2>\n"
            f'\t\t\t\t\t<ul class="kn-link-list">{items}</ul>\n'
            "\t\t\t\t</aside>"
        )

    return f"""<!DOCTYPE HTML>
<html lang="en">
<head>
\t<meta charset="utf-8" />
\t<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
\t<title>{html.escape(post.title)} — Paper Notes — Jipeng Sun</title>
{seo_block(title=post.title, description=description, canonical=post.canonical, jsonld=jsonld)}
\t<link rel="stylesheet" href="{prefix}assets/css/main.css" />
\t<link rel="stylesheet" href="{prefix}assets/css/knowledge-article.css" />
{ga_snippet(prefix)}
</head>
<body class="is-preload kn-page">
\t<div id="wrapper">
{header}
{menu}
\t\t<div id="main">
\t\t\t<article class="post">
\t\t\t\t<header><div class="title"><h1>{html.escape(post.title)}</h1></div></header>
\t\t\t\t<p class="kn-back"><a href="{prefix}blog/index.html">&larr; Paper Notes archive</a>
\t\t\t\t\t<span class="kn-date">{post.date.strftime("%B %-d, %Y")}</span></p>
\t\t\t\t<div class="kn-body">
{body_html}
\t\t\t\t</div>{related_html}
\t\t\t\t<p class="kn-back"><a href="{prefix}knowledge-share.html">
\t\t\t\t\tNewer notes are published in Knowledge Share &rarr;</a></p>
\t\t\t</article>
\t\t</div>
\t</div>
{scripts(prefix)}
</body>
</html>
"""


def render_index(posts: list[Post]) -> str:
    prefix = "../"
    header, menu = chrome(prefix, active="")
    description = (
        f"Archive of {len(posts)} paper reading notes by {AUTHOR} (2022) on transformers, "
        "diffusion models, GANs, and holographic displays."
    )
    canonical = BASE_URL + "/blog/index.html"
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": f"{AUTHOR} — Paper Notes",
        "url": canonical,
        "description": description,
        "author": {"@type": "Person", "name": AUTHOR, "url": BASE_URL + "/"},
    }

    rows = "\n".join(
        f"""\t\t\t\t\t<li class="ks-story">
\t\t\t\t\t\t<a class="ks-story-link" href="{p.year}/{p.month}/{p.day}/{p.slug}.html">
\t\t\t\t\t\t\t<div class="ks-story-body">
\t\t\t\t\t\t\t\t<span class="ks-story-kicker">{p.date.strftime("%B %Y")}</span>
\t\t\t\t\t\t\t\t<span class="ks-story-title">{html.escape(p.title)}</span>
\t\t\t\t\t\t\t\t<span class="ks-story-dek">{html.escape(derive_description(p.body, p.title))}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</a>
\t\t\t\t\t</li>"""
        for p in posts
    )

    return f"""<!DOCTYPE HTML>
<html lang="en">
<head>
\t<meta charset="utf-8" />
\t<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
\t<title>Paper Notes Archive — Jipeng Sun</title>
{seo_block(title="Paper Notes Archive — Jipeng Sun", description=description, canonical=canonical, jsonld=jsonld)}
\t<link rel="stylesheet" href="{prefix}assets/css/main.css" />
\t<link rel="stylesheet" href="{prefix}assets/css/knowledge-share.css" />
\t<link rel="stylesheet" href="{prefix}assets/css/knowledge-article.css" />
{ga_snippet(prefix)}
</head>
<body class="is-preload ks-page">
\t<div id="wrapper">
{header}
{menu}
\t\t<div id="main">
\t\t\t<section class="ks-intro">
\t\t\t\t<h1>Paper Notes Archive</h1>
\t\t\t\t<p>Reading notes I wrote in 2022 while working through papers on sequence models,
\t\t\t\t\ttransformers, generative models, and holographic displays. Each note follows the same
\t\t\t\t\tshape: summary, strengths, critique, and the resources I found useful.</p>
\t\t\t\t<p>These are kept online because people still link to them. Newer notes live in
\t\t\t\t\t<a href="{prefix}knowledge-share.html">Knowledge Share</a>.</p>
\t\t\t</section>
\t\t\t<ol class="ks-story-list">
{rows}
\t\t\t</ol>
\t\t</div>
\t</div>
{scripts(prefix)}
</body>
</html>
"""


def run() -> None:
    posts = load_posts()
    if not posts:
        print("no posts found in _posts/")
        return

    for idx, post in enumerate(posts):
        # Cross-link each post to its neighbours so no post is a dead end.
        related = [p for p in (posts[idx - 1] if idx else None, *posts[idx + 1: idx + 3]) if p]
        post.out_path.parent.mkdir(parents=True, exist_ok=True)
        post.out_path.write_text(render_post(post, related), encoding="utf-8")

    (BLOG / "index.html").write_text(render_index(posts), encoding="utf-8")
    print(f"blog: wrote {len(posts)} posts + blog/index.html")


if __name__ == "__main__":
    run()
