#!/usr/bin/env python3
"""Convert Notion MCP <content> markdown-ish text to safe HTML fragments."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

NOTION_TO_SLUG: dict[str, str] = {
    "31701d9f5287800389c5d2da8aa83874": "robotics",
    "31701d9f52878046a137f3a1df660d09": "world-models",
    "31701d9f5287804d82e1fa6fb1a684f7": "flow-matching",
    "31701d9f5287807c9ee3cc590ab568e1": "math",
    "31701d9f528780deb467c76c3b117c63": "machine-learning",
    "31801d9f52878017a966fe9c0b3fb4dd": "generative-methods-for-deconv",
    "31a01d9f528780459aa0dd0527ab6873": "computational-imaging",
    "31a01d9f52878048ae50fab695d977cb": "pnp-with-diffusion",
    "31a01d9f5287804cb1baea8ce98a4d71": "diffusion-from-sdes",
    "32b01d9f5287801499f9f5a715df87b1": "diffusion-model",
    "32c01d9f52878006a8e4dee9db27dd3d": "ddpms-ddims-amp-score-based",
    "32c01d9f528780238102c422cb28845c": "kl-divergence",
    "32c01d9f5287804792e1da18a5b91188": "elbo",
    "32c01d9f52878062a470f201d04b52b8": "classifier-free-guidance",
    "32c01d9f528780789c4ff2887d8083bf": "ddim",
    "32c01d9f528780c998eeffe7cf6a3ee9": "vae-vs-diffusion-elbo",
    "33001d9f5287801ba5ccd81fa27b4263": "optimization",
    "33001d9f5287806db4bef231ce5d0355": "admm",
    "33001d9f528780c19fd8c8afabbc1edc": "geometry-generation",
    "33301d9f52878014b40ff77d90d4ae7b": "proximal-algorithms",
    "33301d9f52878038a6f0d88e61ba2406": "hqs",
    "33301d9f5287806d911bd48dbf8729cf": "analytical-proximal-operators",
    "33301d9f5287807dbac3cc0b43950e45": "neural-proximal-operators",
    "33301d9f5287808b81ace1893b7a4282": "lagrangian-method",
    "33401d9f52878085af98de3ec4befad3": "lucas-kanade-example",
    "33401d9f528780b6905cfccf8865e1ce": "raft",
    "33401d9f528780b996e0fb59323b447f": "optical-flow",
    "33401d9f528780c695b4db4ec21ea13a": "computer-vision",
    "33601d9f5287804f95a7fed3efafb131": "mean-flow",
    "33901d9f52878061b15ce12ba00b5a33": "improved-mean-flow-imf",
    "33b01d9f52878023ae1fdd9460f81992": "self-attention",
    "33b01d9f5287806f9ce5f06def87d02a": "vision-transformer-vit",
    "33b01d9f528780809920d77feccea568": "classifier-free-guidance-cfg",
    "33b01d9f52878094a2f1d26eeebe0983": "diffusion-transformer-dit",
    "34901d9f5287801981a7e6a7eab9ddc5": "backpropagation",
    "34901d9f528780b8a125f62ee430ac4d": "camera-intrinsic-matrix",
    "34901d9f528780e69a8fe7e6a50c7fa9": "autodiff",
    "34a01d9f5287803f9dd9c7b0fe8b759b": "bundle-adjustment",
    "35501d9f5287801e9a5ce5862e81f512": "nerf",
    "35501d9f528780ab9d0efc6831a5611e": "camera-extrinsic-matrix",
    "35501d9f528780dabe98fe56ccb15d78": "3d-gaussian-splatting",
    "35501d9f528780ddafd2dcb09d9a6cb7": "computer-graphics",
    "35601d9f528780b1bebcdb71d1a4286a": "colmap",
}


def extract_from_mcp_view(raw: str) -> tuple[str, str]:
    title = "Untitled"
    m_prop = re.search(r"<properties>\s*(\{[^<]*\})\s*</properties>", raw, re.DOTALL)
    if m_prop:
        blob = m_prop.group(1).strip()
        try:
            title = json.loads(blob).get("title", title)
        except json.JSONDecodeError:
            m_t = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', blob)
            if m_t:
                title = m_t.group(1).replace(r"\"", '"').replace(r"\\", "\\")
    m_c = re.search(r"<content>\s*([\s\S]*?)\s*</content>", raw)
    body = m_c.group(1).strip() if m_c else ""
    return title, body


MENTION_PAGE = re.compile(
    r'<mention-page url="https://(?:www\.notion\.so/|app\.notion\.com/p/)([a-f0-9]{32})"\s*/>',
)


def _title_from_raw(pid: str) -> str | None:
    raw_path = Path(__file__).resolve().parents[1] / "knowledge" / "raw" / f"{pid}.txt"
    if not raw_path.is_file():
        return None
    title, _ = extract_from_mcp_view(raw_path.read_text(encoding="utf-8"))
    return title if title and title != "Untitled" else None


def replace_mentions(md: str) -> str:
    def humanize_slug(slug: str) -> str:
        return " ".join(slug.replace("-", " ").split()).title()

    def repl(m: re.Match[str]) -> str:
        pid = m.group(1)
        slug = NOTION_TO_SLUG.get(pid)
        if not slug:
            return m.group(0)
        label = _title_from_raw(pid) or humanize_slug(slug)
        return f"[{label}]({slug}.html)"

    return MENTION_PAGE.sub(repl, md)


INLINE_TOK = re.compile(
    r"(\$`[^`]+`\$|\*\*.+?\*\*|`.+?`|\[[^\]]*\]\([^)]*\))"
)

INLINE_MATH_ONLY = re.compile(r"^\$`([^`]+)`\$")
DISPLAY_MATH_ONLY = re.compile(r"^\$\$([\s\S]+?)\$\$$")
ESCAPED_DISPLAY_MATH = re.compile(r"^\\\$\\\$((?:[^\\]|\\.)+?)\\\$\\\$$")
ESCAPED_INLINE_MATH = re.compile(r"^\\\$((?:[^\\]|\\.)+?)\\\$$")
KATEX_INLINE_LINE = re.compile(r"^\\\(([\s\S]+?)\\\)$")
KATEX_DISPLAY_LINE = re.compile(r"^\\\[([\s\S]+?)\\\]$")


def unescape_notion_latex(tex: str) -> str:
    """Convert Notion-escaped LaTeX (\\mathbb\\{R\\}) to KaTeX-ready form."""
    tex = tex.replace(r"\{", "{").replace(r"\}", "}")
    tex = tex.replace(r"\^", "^").replace(r"\_", "_")
    while "\\\\" in tex:
        tex = tex.replace("\\\\", "\\")
    return tex.strip()


def normalize_tex(tex: str) -> str:
    return unescape_notion_latex(tex)


def inline_math(tex: str) -> str:
    """KaTeX inline delimiter without HTML wrapper (auto-render friendly)."""
    return r"\(" + normalize_tex(tex) + r"\)"


def display_math(tex: str) -> str:
    """KaTeX display delimiter."""
    return r"\[" + normalize_tex(tex) + r"\]"


def is_standalone_math_line(line: str) -> str | None:
    st = line.strip()
    for pat in (
        INLINE_MATH_ONLY,
        DISPLAY_MATH_ONLY,
        ESCAPED_DISPLAY_MATH,
        ESCAPED_INLINE_MATH,
        KATEX_DISPLAY_LINE,
        KATEX_INLINE_LINE,
    ):
        m = pat.match(st)
        if m:
            return normalize_tex(m.group(1))
    return None


def inline_format_text(text: str) -> str:
    """Inline **bold**, `code`, [text](url), $`tex`$ → HTML (math passed through for KaTeX)."""
    result: list[str] = []
    pos = 0
    for m in INLINE_TOK.finditer(text):
        if m.start() > pos:
            result.append(html.escape(text[pos : m.start()], quote=False))
        tok = m.group(1)
        if tok.startswith("$`") and tok.endswith("`$"):
            tex = tok[2:-2].strip()
            result.append(inline_math(tex))
        elif tok.startswith("**") and tok.endswith("**"):
            result.append("<strong>" + html.escape(tok[2:-2], quote=False) + "</strong>")
        elif tok.startswith("`") and tok.endswith("`"):
            result.append("<code>" + html.escape(tok[1:-1], quote=False) + "</code>")
        elif tok.startswith("["):
            m2 = re.match(r"\[([^\]]*)\]\(([^)]*)\)", tok)
            if m2:
                lab, href = m2.group(1), m2.group(2)
                lab_html = inline_format_text(lab) if lab else ""
                eh = html.escape(href, quote=True)
                if href.startswith("http://") or href.startswith("https://"):
                    result.append(
                        f'<a href="{eh}" target="_blank" rel="noopener">{lab_html}</a>'
                    )
                else:
                    result.append(f'<a href="{eh}">{lab_html}</a>')
            else:
                result.append(html.escape(tok, quote=False))
        else:
            result.append(html.escape(tok, quote=False))
        pos = m.end()
    if pos < len(text):
        result.append(html.escape(text[pos:], quote=False))
    return "".join(result)


IMG_LINE = re.compile(r"^!\[\]\(([^)]+)\)$")
LINK_ONLY = re.compile(r"^\[[^\]]*\]\(([^)]+\.html)\)$")


def parse_link_only(line: str) -> tuple[str, str] | None:
    m = LINK_ONLY.match(line.strip())
    if not m:
        return None
    m2 = re.match(r"^\[([^\]]*)\]\(([^)]+\.html)\)$", line.strip())
    if not m2:
        return None
    return m2.group(1), m2.group(2)


def render_link_list(items: list[tuple[str, str]]) -> str:
    lis = []
    for lab, href in items:
        eh = html.escape(href, quote=True)
        lab_html = inline_format_text(lab)
        lis.append(f'<li><a href="{eh}">{lab_html}</a></li>')
    return '<ul class="kn-link-list">' + "".join(lis) + "</ul>"


def replace_notion_math(md: str) -> str:
    """Notion exports math as $`...`$, \\$...\\$, or \\$\\$...\\$\\$ with escaped braces."""

    def disp(m: re.Match[str]) -> str:
        return display_math(m.group(1))

    def inl(m: re.Match[str]) -> str:
        return inline_math(m.group(1))

    md = re.sub(r"\\\$\\\$((?:[^\\]|\\.)+?)\\\$\\\$", disp, md)
    md = re.sub(r"\\\$((?:[^\\]|\\.)+?)\\\$", inl, md)
    return md


def notion_body_to_html(md: str) -> str:
    md = replace_mentions(md)
    md = replace_notion_math(md)
    md = re.sub(r"<empty-block/>", "\n\n", md)
    md = md.replace("\r\n", "\n")

    blocks: list[str] = []
    lines = md.split("\n")
    n = len(lines)
    i = 0

    def flush_para(buf: list[str]) -> None:
        if not buf:
            return

        stripped = [line.strip() for line in buf if line.strip()]
        if stripped and all(parse_link_only(line) for line in stripped):
            blocks.append(render_link_list([parse_link_only(line) for line in stripped]))  # type: ignore[misc]
            return

        def flush_shorts(shorts: list[str]) -> None:
            if not shorts:
                return
            if len(shorts) == 1:
                blocks.append("<p>" + inline_format_text(shorts[0]) + "</p>")
            else:
                for s in shorts:
                    blocks.append("<p>" + inline_format_text(s) + "</p>")

        shorts: list[str] = []
        for line in buf:
            st = line.strip()
            if not st:
                continue
            if len(st) > 220:
                flush_shorts(shorts)
                shorts = []
                if "$$" in st:
                    segs = re.split(r"(\$\$[\s\S]*?\$\$)", st)
                    for seg in segs:
                        if seg.startswith("$$") and seg.endswith("$$"):
                            tex = seg[2:-2].strip()
                            blocks.append(f'<p class="kn-math-display">{display_math(tex)}</p>')
                        elif seg.strip():
                            blocks.append("<p>" + inline_format_text(seg.strip()) + "</p>")
                else:
                    blocks.append("<p>" + inline_format_text(st) + "</p>")
            else:
                shorts.append(st)
        flush_shorts(shorts)

    buf: list[str] = []
    while i < n:
        line = lines[i]
        st = line.strip()
        if not st:
            flush_para(buf)
            buf = []
            i += 1
            continue
        if st == "---":
            flush_para(buf)
            buf = []
            blocks.append("<hr />")
            i += 1
            continue
        math_tex = is_standalone_math_line(st)
        if math_tex is not None:
            flush_para(buf)
            buf = []
            blocks.append(f'<p class="kn-math-display">{display_math(math_tex)}</p>')
            i += 1
            continue
        mimg = IMG_LINE.match(st)
        if mimg:
            flush_para(buf)
            buf = []
            src = html.escape(mimg.group(1).strip(), quote=True)
            blocks.append(f'<figure class="kn-figure"><img src="{src}" alt="" loading="lazy" /></figure>')
            i += 1
            continue
        mh = re.match(r"(#{1,6})\s+(.*)$", st)
        if mh:
            flush_para(buf)
            buf = []
            lv = min(len(mh.group(1)), 6)
            tag = f"h{lv}"
            blocks.append(f"<{tag}>{inline_format_text(mh.group(2).strip())}</{tag}>")
            i += 1
            continue
        link_item = parse_link_only(st)
        if link_item:
            flush_para(buf)
            buf = []
            link_items: list[tuple[str, str]] = [link_item]
            i += 1
            while i < n:
                nxt = parse_link_only(lines[i].strip())
                if not nxt:
                    break
                link_items.append(nxt)
                i += 1
            blocks.append(render_link_list(link_items))
            continue
        if st.startswith("- "):
            flush_para(buf)
            buf = []
            items: list[str] = []
            while i < n and lines[i].strip().startswith("- "):
                item = lines[i].strip()[2:].strip()
                items.append(f"<li>{inline_format_text(item)}</li>")
                i += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", st):
            flush_para(buf)
            buf = []
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i].strip())
                items.append(f"<li>{inline_format_text(item)}</li>")
                i += 1
            blocks.append("<ol>" + "".join(items) + "</ol>")
            continue
        buf.append(st)
        i += 1
    flush_para(buf)
    return "\n".join(blocks)


def build_full_page(title: str, inner_html: str, slug: str) -> str:
    nav_back = "../../knowledge-share.html"
    return f"""<!DOCTYPE HTML>
<html lang="en">
<head>
\t<meta charset="utf-8" />
\t<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
\t<title>{html.escape(title)} — Knowledge Share — Jipeng Sun</title>
\t<link rel="stylesheet" href="../../assets/css/main.css" />
\t<link rel="stylesheet" href="../../assets/css/knowledge-article.css" />
\t<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" crossorigin="anonymous" />
\t<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" crossorigin="anonymous"></script>
\t<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" crossorigin="anonymous" onload="(function(){{var b=document.querySelector('.kn-body');if(!b)return;b.querySelectorAll('span').forEach(function(s){{if(s.children.length)return;var t=s.textContent.trim();if(/^\\\\\\([\\s\\S]*\\\\\\)$/.test(t)||/^\\\\\\[[\\s\\S]*\\\\\\]$/.test(t))s.replaceWith(document.createTextNode(t));}});renderMathInElement(b,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'\\\\(',right:'\\\\)',display:false}},{{left:'\\\\[',right:'\\\\]',display:true}}],throwOnError:false,ignoredTags:['script','noscript','style','textarea','pre','code']}});}})();"></script>
\t<script async src="https://www.googletagmanager.com/gtag/js?id=G-LCC4R0HD24"></script>
\t<script>
\t  window.dataLayer = window.dataLayer || [];
\t  function gtag(){{dataLayer.push(arguments);}}
\t  gtag('js', new Date());
\t  gtag('config', 'G-LCC4R0HD24');
\t</script>
\t<script src="../../assets/js/ga-events.js"></script>
</head>
<body class="is-preload kn-page">
\t<div id="wrapper">
\t\t<header id="header">
\t\t\t<h1><a href="../../index.html">Jipeng Sun</a></h1>
\t\t\t<nav class="links">
\t\t\t\t<ul>
\t\t\t\t\t<li><a href="../../index.html">Home</a></li>
\t\t\t\t\t<li><a href="../../research.html">Research</a></li>
\t\t\t\t\t<li class="active"><a href="{nav_back}">Knowledge Share</a></li>
\t\t\t\t\t<li><a href="https://sites.northwestern.edu/cs396vrsystems/" data-ga-event="vr_ar_course">VR/AR Course</a></li>
\t\t\t\t</ul>
\t\t\t</nav>
\t\t\t<nav class="main">
\t\t\t\t<ul>
\t\t\t\t\t<li class="search"><a class="fa-search" href="#search">Search</a><form id="search" method="get" action="#"><input type="text" name="query" placeholder="Search" /></form></li>
\t\t\t\t\t<li class="menu"><a class="fa-bars" href="#menu">Menu</a></li>
\t\t\t\t</ul>
\t\t\t</nav>
\t\t</header>
\t\t<section id="menu">
\t\t\t<section><form class="search" method="get" action="#"><input type="text" name="query" placeholder="Search" /></form></section>
\t\t\t<section>
\t\t\t\t<ul class="links">
\t\t\t\t\t<li><a href="../../index.html"><h3>Home</h3><p>Jipeng Sun's Homepage</p></a></li>
\t\t\t\t\t<li><a href="../../research.html"><h3>Research</h3><p>Publications &amp; Papers</p></a></li>
\t\t\t\t\t<li><a href="{nav_back}"><h3>Knowledge Share</h3><p>Study notes</p></a></li>
\t\t\t\t\t<li><a href="https://sites.northwestern.edu/cs396vrsystems/" data-ga-event="vr_ar_course"><h3>Teaching</h3><p>VR Summer Course</p></a></li>
\t\t\t\t</ul>
\t\t\t</section>
\t\t</section>
\t\t<div id="main">
\t\t\t<article class="post">
\t\t\t\t<header><div class="title"><h2>{html.escape(title)}</h2></div></header>
\t\t\t\t<p class="kn-back"><a href="{nav_back}">&larr; Back to Knowledge Share</a></p>
\t\t\t\t<div class="kn-body">
{inner_html}
\t\t\t\t</div>
\t\t\t</article>
\t\t</div>
\t</div>
\t<script src="../../assets/js/jquery.min.js"></script>
\t<script src="../../assets/js/browser.min.js"></script>
\t<script src="../../assets/js/breakpoints.min.js"></script>
\t<script src="../../assets/js/util.js"></script>
\t<script src="../../assets/js/main.js"></script>
</body>
</html>
"""


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("mcp_text_file", type=Path, help="File containing raw notion-fetch text field")
    p.add_argument("out_html", type=Path)
    args = p.parse_args()
    raw = args.mcp_text_file.read_text(encoding="utf-8")
    title, body = extract_from_mcp_view(raw)
    # slug from filename stem convention: slug.html's stem
    slug = args.out_html.stem
    inner = notion_body_to_html(body)
    args.out_html.parent.mkdir(parents=True, exist_ok=True)
    args.out_html.write_text(build_full_page(title, "\t\t\t\t" + inner.replace("\n", "\n\t\t\t\t"), slug), encoding="utf-8")


if __name__ == "__main__":
    main()
