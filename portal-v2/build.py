#!/usr/bin/env python3
"""Build the HR manual app — hr-manual-2.html (and its twin index.html).

Two modes:

  python3 portal-v2/build.py
      Everyday edits. Re-injects portal-v2/app.css and portal-v2/app.js into
      hr-manual-2.html, then writes hr-manual-2.html and index.html (the
      GitHub Pages entry) as identical files. Every chapter section is checked
      to be byte-identical before and after.

  python3 portal-v2/build.py --from <legacy-portal.html>
      Full rebuild from a legacy single-file portal (the original source was
      "Sumedha ma'am requirements /jsw-hr-portal.html" on the Desktop).

Full-rebuild mode carries over from the legacy file (read only, never written):
  * every chapter section's content, byte-for-byte (chapter number and
    title move into the new header; decorative header photos are dropped)
  * the component scripts the content needs (org chart, role directory,
    interactive diagrams — calendar and incentive tabs live inside sections)
  * the TOC array, cover wording, search wording, footer text, logos, favicon
  * the content stylesheet, minus rules that can no longer match anything
    (their classes/ids exist nowhere in the new document or its scripts)

New: portal-v2/shell.html, app.css, app.js.
Every extraction asserts an exact match count, so a changed source stops the
build instead of silently producing a partial file.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
MAIN = HERE.parent / "hr-manual-2.html"
OUTS = [MAIN, HERE.parent / "v2.html"]      # kept byte-identical
SECTION_RE = re.compile(r'<section class="chap" id="[^"]+">.*?</section>', re.S)


def fail(msg):
    sys.exit("build: " + msg)


def one(pattern, text, label, flags=re.S):
    found = re.findall(pattern, text, flags)
    if len(found) != 1:
        fail(f"expected exactly 1 match for {label}, found {len(found)}")
    return found[0]


# --------------------------------------------------------------------------
# CSS dead-rule pruning
# --------------------------------------------------------------------------
def _match_brace(css, i):
    """css[i] == '{' -> index just past the matching '}' (strings/comments aware)."""
    depth, n = 0, len(css)
    while i < n:
        c = css[i]
        if c in "\"'":
            q = c
            i += 1
            while i < n and css[i] != q:
                i += 2 if css[i] == "\\" else 1
        elif css.startswith("/*", i):
            i = css.find("*/", i + 2)
            if i < 0:
                fail("unterminated css comment")
            i += 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    fail("unbalanced css braces")


def _find_top(css, i, chars):
    """First index >= i of any of `chars` outside strings, comments and ( )."""
    depth, n = 0, len(css)
    while i < n:
        c = css[i]
        if c in "\"'":
            q = c
            i += 1
            while i < n and css[i] != q:
                i += 2 if css[i] == "\\" else 1
        elif css.startswith("/*", i):
            i = css.find("*/", i + 2) + 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif depth == 0 and c in chars:
            return i
        i += 1
    return -1


def _selector_live(selector, tokens, prefixes):
    sel = re.sub(r":not\((?:[^()]|\([^()]*\))*\)", "", selector)
    sel = re.sub(r"\[[^\]]*\]", "", sel)
    for kind, name in re.findall(r"([.#])(-?[_a-zA-Z][\w-]*)", sel):
        if name not in tokens and not any(name.startswith(p) for p in prefixes):
            return False
    return True


def prune_css(css, tokens, prefixes=()):
    out, i, n = [], 0, len(css)
    while i < n:
        if css[i].isspace():
            i += 1
            continue
        if css.startswith("/*", i):
            i = css.index("*/", i + 2) + 2
            continue
        brace = _find_top(css, i, "{")
        semi = _find_top(css, i, ";")
        if css[i] == "@" and semi != -1 and (brace == -1 or semi < brace):
            out.append(css[i:semi + 1].strip())          # @import / @charset
            i = semi + 1
            continue
        if brace == -1:
            break
        prelude = css[i:brace].strip()
        end = _match_brace(css, brace)
        body = css[brace + 1:end - 1]
        i = end
        if prelude.startswith("@"):
            name = prelude.split()[0].lower()
            if name in ("@media", "@supports", "@container", "@layer"):
                inner = prune_css(body, tokens, prefixes)
                if inner.strip():
                    out.append(f"{prelude}{{\n{inner}\n}}")
            else:
                out.append(f"{prelude}{{{body}}}")        # keyframes, font-face, page
            continue
        prelude = re.sub(r"/\*.*?\*/", "", prelude, flags=re.S).strip()
        parts, start = [], 0
        while True:
            comma = _find_top(prelude, start, ",")
            if comma == -1:
                parts.append(prelude[start:])
                break
            parts.append(prelude[start:comma])
            start = comma + 1
        live = [s.strip() for s in parts if s.strip() and _selector_live(s, tokens, prefixes)]
        if live:
            out.append(f"{', '.join(live)}{{{body.strip()}}}")
    return "\n".join(out)


def tokens_of(html, scripts):
    toks = set()
    for v in re.findall(r'\bclass="([^"]*)"', html):
        toks.update(v.split())
    toks.update(re.findall(r'\bid="([^"]+)"', html))
    for s in scripts:
        toks.update(re.findall(r"[A-Za-z_][\w-]*", s))
    return toks


def dynamic_prefixes(scripts):
    """Class/id prefixes that scripts complete at runtime, e.g. 'cat-' + name."""
    found = set()
    for s in scripts:
        found.update(re.findall(r"""([A-Za-z_][\w-]*-)['"`]\s*\+""", s))   # 'cat-' + c
        found.update(re.findall(r"([A-Za-z_][\w-]*-)\$\{", s))              # `cat-${c}`
    return found


def write_outputs(body):
    for out in OUTS:
        out.write_text(body, encoding="utf-8")
    return ", ".join(o.name for o in OUTS)


def swap_block(html, open_tag, new_inner, label):
    """Replace the inner text of the single element that opens with open_tag."""
    if html.count(open_tag) != 1:
        fail(f"expected exactly 1 {label} block, found {html.count(open_tag)}")
    start = html.index(open_tag) + len(open_tag)
    close = "</style>" if open_tag.startswith("<style") else "</script>"
    end = html.index(close, start)
    return html[:start] + "\n" + new_inner + html[end:]


# --------------------------------------------------------------------------
def update():
    html = MAIN.read_text(encoding="utf-8")
    before = SECTION_RE.findall(html)
    if len(before) != 15:
        fail(f"expected 15 chapter sections in {MAIN.name}, found {len(before)}")
    app_css = (HERE / "app.css").read_text(encoding="utf-8")
    app_js = (HERE / "app.js").read_text(encoding="utf-8")
    html = swap_block(html, '<style id="jx-app-css">', app_css, "app css")
    html = swap_block(html, '<script id="jx-app-js">', app_js, "app js")
    if SECTION_RE.findall(html) != before:
        fail("chapter content changed during update")
    names = write_outputs(html)
    print(f"build: updated {names} ({len(html):,} bytes); 15 chapters byte-identical")


def full_build(src_path):
    src = pathlib.Path(src_path).read_text(encoding="utf-8")
    shell = (HERE / "shell.html").read_text(encoding="utf-8")
    app_css = (HERE / "app.css").read_text(encoding="utf-8")
    app_js = (HERE / "app.js").read_text(encoding="utf-8")

    favicon = one(r'(<link rel="icon"[^>]*>)', src, "favicon")
    content_css = one(r"<style>(.*?)</style>", src, "content stylesheet")
    logo_light = one(r'<img src="(data:[^"]+)" alt="JSW" class="tb-logo-img">', src, "light logo")
    logo_dark = one(r'<img src="(data:[^"]+)" alt="JSW" class="foot-logo-img">', src, "dark logo")

    # cover wording
    cover = one(r'<header class="cover" id="cover">(.*?)</header>', src, "cover")
    eyebrow = one(r'<div class="eyebrow">(.*?)</div>', cover, "cover eyebrow")
    line = one(r'<span class="ht-line solid">(.*?)</span>', cover, "cover title line")
    word = one(r'<span class="ht-line outline">(.*?)</span>', cover, "cover title word")
    pillars = re.findall(r'<li><span class="tr-w"><span class="tr-i">(.)</span>(.*?)</span></li>', cover)
    if len(pillars) != 5:
        fail(f"expected 5 cover pillars, found {len(pillars)}")
    quote = one(r'<p class="hero-quote">(.*?)</p>', cover, "cover quote")
    letters = "".join(f'<span aria-hidden="true" style="--i:{k}">{ch}</span>' for k, ch in enumerate(word))
    pillars_html = "\n".join(
        f'          <li style="--i:{k}"><b>{a}</b>{b}</li>' for k, (a, b) in enumerate(pillars))

    # search wording
    placeholder = one(r'id="searchInput" placeholder="([^"]*)"', src, "search placeholder")
    hint = re.findall(r'<div class="search-hint">(Type to start[^<]*)</div>', src)
    if not hint:
        fail("search hint not found")
    if src.count("No matching policies found for \"' + query + '\"") != 1:
        fail("search empty-state wording changed")
    empty = 'No matching policies found for &quot;{q}&quot;'

    foot_text = one(r'<div class="manual-foot-text">\s*(.*?)\s*</div>', src, "footer text")

    # chapters
    sec_re = re.compile(r'<section class="chap(?: alt)?" id="([^"]+)">(.*?)</section>', re.S)
    sections = sec_re.findall(src)
    if len(sections) != 15 or src.count("</section>") != 15:
        fail(f"expected 15 chapter sections, found {len(sections)}")
    head_re = re.compile(
        r'^\s*<div class="chap-head reveal">\s*<div class="chap-num">(.*?)</div>\s*'
        r'<h2 class="sec-title">(.*?)</h2>\s*<div class="rule"></div>\s*'
        r'(?:<div class="ch-thumb"[^>]*></div>\s*)?</div>', re.S)
    chapter_html, content_blocks = [], []
    for sid, inner in sections:
        m = head_re.match(inner)
        if not m:
            fail(f"unexpected chapter head in #{sid}")
        num, title = m.group(1), m.group(2)
        rest = inner[m.end():]
        content_blocks.append(rest)
        chapter_html.append(
            f'    <article class="jx-chapter" id="chap-{sid}" hidden>\n'
            f'      <header class="jx-head"><div class="jx-head-row"><div>'
            f'<p class="jx-kicker">{num}</p><h1 class="jx-h1">{title}</h1>'
            f'</div></div></header>\n'
            f'      <section class="chap" id="{sid}">{rest}</section>\n'
            f'    </article>')

    # component scripts that sit between sections, plus the diagram layer
    comp = []
    comp.append(one(r"(<script>\s*window\.ORG_CATEGORIES = .*?</script>)", src, "org chart script"))
    comp.append(one(r"(<script>\s*\(function\(\)\{\s*var activeRoleIndex = -1;.*?</script>)", src, "role directory script"))
    comp.append(one(r"(<script>\s*\(function\(\) \{\s*function initInteractiveDiagrams\(\).*?</script>)", src, "diagram script"))

    toc = one(r"const TOC = (\[.*?\n\]);", src, "TOC")

    body = shell
    for key, val in {
        "{{FAVICON}}": favicon,
        "{{LOGO_LIGHT}}": logo_light,
        "{{LOGO_DARK}}": logo_dark,
        "{{HERO_EYEBROW}}": eyebrow,
        "{{HERO_LINE}}": line,
        "{{HERO_WORD}}": word,
        "{{HERO_WORD_LETTERS}}": letters,
        "{{HERO_PILLARS}}": pillars_html,
        "{{HERO_QUOTE}}": quote,
        "{{SEARCH_PLACEHOLDER}}": placeholder,
        "{{SEARCH_HINT}}": hint[0],
        "{{SEARCH_EMPTY}}": empty,
        "{{FOOT_TEXT}}": foot_text,
        "{{CHAPTERS}}": "\n".join(chapter_html),
        "{{COMPONENT_SCRIPTS}}": "\n".join(comp),
        "{{TOC}}": f"window.JX_TOC = {toc};",
        "{{APP_JS}}": app_js,
    }.items():
        if key not in body:
            fail(f"placeholder {key} missing from shell")
        body = body.replace(key, val)

    scripts = re.findall(r"<script[^>]*>(.*?)</script>", body, re.S)
    handlers = re.findall(r'\bon\w+="([^"]*)"', body)
    tokens = tokens_of(re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.S), scripts + handlers)
    prefixes = dynamic_prefixes(scripts + handlers)
    pruned = prune_css(content_css, tokens, prefixes)

    body = body.replace("{{CONTENT_CSS}}", pruned).replace("{{APP_CSS}}", app_css)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", body)
    if leftover:
        fail(f"unfilled placeholders: {leftover}")

    # content must be byte-identical inside the output
    for block in content_blocks:
        if block not in body:
            fail("a chapter's content block was altered during assembly")

    names = write_outputs(body)
    print(f"build: wrote {names} ({len(body):,} bytes); "
          f"content css {len(content_css):,} -> {len(pruned):,} chars; 15 chapters verbatim")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--from":
        full_build(sys.argv[2])
    elif len(sys.argv) == 1:
        update()
    else:
        fail("usage: build.py  |  build.py --from <legacy-portal.html>")
