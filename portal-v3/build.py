#!/usr/bin/env python3
"""Build v3.html — the greyscale, background-integrated edition.

Sources (read from git so the build is repeatable):
  * v3 base  : v3.html at commit BASE (home markup: hero, pills, quick menu)
  * v2 clean : v2.html at HEAD (the manual's original content stylesheet and
               the three content lines that the earlier v3 pass had repainted
               white; restoring them brings back visible accents, which are
               then greyed below)
  * portal-v3/v3.css : the new design layer (replaces the old override block)

Every colour literal in stylesheets, style="" attributes, SVG colour
attributes and script colour strings is mapped to a neutral grey of equal
luminance. The manual's gold accent family is mapped to the dark end of the
reference ramp instead, so accents stay legible on the light ground.

The build refuses to write if any visible text, id, href or data-* attribute
differs from the base file.
"""
import re, subprocess, sys, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = '0a430bb'
OUT = ROOT / 'v3.html'

def git_show(rev, path):
    return subprocess.run(['git', 'show', f'{rev}:{path}'], cwd=ROOT, check=True,
                          capture_output=True).stdout.decode('utf-8')

v3 = git_show(BASE, 'v3.html')
v2 = git_show('HEAD', 'v2.html')

# ---------------------------------------------------------------- 0 home layout
# The manual's name lives only in the top strip; the home page opens straight
# on the chapter cards (no big title hero, no "Direct chapter access" grid).
TITLE = 'JSW HR Operations Manual: TRUST'

def cut(s, start, end):
    i = s.index(start); j = s.index(end, i)
    return s[:i] + s[j:]

def home_layout(s):
    s = cut(s, '      <div class="jx-hero">', '      <!-- Quick Action Navigation Bar on First Page -->')
    s = cut(s, '      <!-- Direct Chapter Access Grid -->', '      <div class="jx-seg"')
    cards = ('      <div class="jx-seg" id="jxSeg" role="tablist" aria-label="Filter by part"><i class="jx-seg-ind" aria-hidden="true"></i></div>\n'
             '      <div class="jx-cards" id="jxCards"></div>\n')
    assert s.count(cards) == 1
    s = s.replace(cards, '')
    head = '    <section class="jx-home" id="jxHome" aria-label="Home">\n'
    assert s.count(head) == 1
    s = s.replace(head, head + f'      <h1 class="jx-sr">{TITLE}</h1>\n' + cards + '\n')
    # the name in the strip: sidebar head on desktop, top bar on phones
    s = s.replace('      <span>HR Operations Manual</span>\n', f'      <span>{TITLE}</span>\n', 1)
    top = re.search(r'(<button class="jx-top-brand"[^>]*>\s*<img [^>]*>)(\s*</button>)', s)
    s = s[:top.end(1)] + f'<span class="jx-top-title">{TITLE}</span>' + s[top.end(1):]
    return s


# ---------------------------------------------------------------- 1 restore
def block(s, tag):
    m = re.search(r'(<style id="%s">)(.*?)(</style>)' % tag, s, re.S)
    assert m, tag
    return m

v2l, v3l = v2.split('\n'), v3.split('\n')
# content lines whose inline colours the earlier pass replaced with white;
# they must be identical once colour literals are masked
mask = lambda s: re.sub(r'#[0-9a-fA-F]{3,6}\b|rgba?\([^)]*\)', 'C', s)
for a, b in [(4113, 5111), (5492, 6490), (5507, 6505)]:
    assert v3l[b - 1] != v2l[a - 1] and mask(v3l[b - 1]) == mask(v2l[a - 1]), (a, b)
    v3l[b - 1] = v2l[a - 1]
v3 = '\n'.join(v3l)

v3 = v3.replace(block(v3, 'jsw-content-css').group(2), block(v2, 'jsw-content-css').group(2), 1)
v3 = home_layout(v3)

# drop the old override block; the new layer goes in its place
old = re.search(r'\n<style id="jx-v3-monochrome-overrides">.*?</style>', v3, re.S)
assert old
css = (ROOT / 'portal-v3' / 'v3.css').read_text()
v3 = v3[:old.start()] + '\n<style id="jx-v3-mono">\n' + css + '</style>' + v3[old.end():]

# Opening a page link directly (#fm-i, #ch2 …) let the browser's own fragment
# scroll jump to the <section> with that id after load, hiding the page title
# under the top bar. Re-apply the router's scroll once the page has loaded.
JS_OLD = "  route({ inPlace: true });\n})();"
JS_NEW = ("  route({ inPlace: true });\n"
          "  window.addEventListener('load', function(){\n"
          "    if(pageIndex[decodeURIComponent(location.hash.slice(1))]) route({ inPlace: true });\n"
          "  });\n})();")
assert v3.count(JS_OLD) == 1
v3 = v3.replace(JS_OLD, JS_NEW)

# "Continue reading" used to hang off the hero; it now follows the cards
JS_OLD = ("    var hero = $('.jx-hero', homeEl);\n"
          "    hero.parentNode.insertBefore(resumeBtn, hero.nextSibling);")
JS_NEW = ("    var actions = $('.jx-home-actions', homeEl);\n"
          "    actions.parentNode.insertBefore(resumeBtn, actions);")
assert v3.count(JS_OLD) == 1
v3 = v3.replace(JS_OLD, JS_NEW)

# ---------------------------------------------------------------- 2 greyscale
ACCENT = {  # manual gold family -> dark end of the reference ramp
    (0xC5, 0xA0, 0x59): '363636', (0xDF, 0xBE, 0x7A): '717171',
    (0x9A, 0x6B, 0x0A): '1B1B1B', (0xD9, 0xA4, 0x41): '717171',
    (0xB8, 0x86, 0x0B): '505050', (0xC9, 0xB8, 0x92): '909090',
    (0xD4, 0xA0, 0x17): '505050', (0xD9, 0xA4, 0x41): '717171',
}

def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def unlin(y):
    v = 12.92 * y if y <= 0.0031308 else 1.055 * y ** (1 / 2.4) - 0.055
    return max(0, min(255, round(v * 255)))

def grey(r, g, b):
    if max(r, g, b) - min(r, g, b) <= 2:
        return None
    if (r, g, b) in ACCENT:
        return ACCENT[(r, g, b)]
    y = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return '%02X' % unlin(y) * 3

HEX = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])')
RGB = re.compile(r'(rgba?\(\s*)(\d{1,3})(\s*,\s*)(\d{1,3})(\s*,\s*)(\d{1,3})')
log = {}

def colours(text, region):
    def h(m):
        x = m.group(1)
        if len(x) == 3:
            x = ''.join(c * 2 for c in x)
        r, g, b = (int(x[i:i + 2], 16) for i in (0, 2, 4))
        n = grey(r, g, b)
        if not n:
            return m.group(0)
        log.setdefault(region, set()).add((m.group(0), '#' + n))
        return '#' + n
    def rg(m):
        r, g, b = int(m.group(2)), int(m.group(4)), int(m.group(6))
        n = grey(r, g, b)
        if not n:
            return m.group(0)
        v = int(n[:2], 16)
        log.setdefault(region, set()).add(((r, g, b), v))
        return f'{m.group(1)}{v}{m.group(3)}{v}{m.group(5)}{v}'
    return RGB.sub(rg, HEX.sub(h, text))

def css_values(css, region):
    # only touch declaration values: a hex whose next structural char is '{'
    # sits in a selector (#id) and is left alone
    out, i = [], 0
    for m in HEX.finditer(css):
        nxt = re.search(r'[{;}]', css[m.end():])
        if nxt and nxt.group(0) == '{':
            # …unless it is inside a [style*="…"] matcher, which must follow
            # the inline styles it targets
            lb = css.rfind('[', 0, m.start())
            if not (lb > css.rfind(']', 0, m.start()) and css.startswith('[style', lb)):
                continue
        out.append(css[i:m.start()]); out.append(colours(m.group(0), region)); i = m.end()
    out.append(css[i:])
    return RGB.sub(lambda m: colours(m.group(0), region), ''.join(out))

def transform(doc):
    parts = re.split(r'(<style\b[^>]*>.*?</style>|<script\b[^>]*>.*?</script>)', doc, flags=re.S)
    res = []
    for p in parts:
        if p.startswith('<style'):
            res.append(css_values(p, 'css'))
        elif p.startswith('<script'):
            # colour strings inside quotes: '#B8860B', "rgba(…)", fill="#…"
            p = re.sub(r"""(['"])(#[0-9a-fA-F]{3,6}|rgba?\([^'"]*\))\1""",
                       lambda m: m.group(1) + colours(m.group(2), 'js') + m.group(1), p)
            p = re.sub(r'(style=\\?")([^"\\]*)', lambda m: m.group(1) + colours(m.group(2), 'js'), p)
            res.append(p)
        else:
            p = re.sub(r'(\sstyle=")([^"]*)(")', lambda m: m.group(1) + colours(m.group(2), 'style') + m.group(3), p)
            p = re.sub(r"(\sstyle=')([^']*)(')", lambda m: m.group(1) + colours(m.group(2), 'style') + m.group(3), p)
            p = re.sub(r'(\s(?:fill|stroke|stop-color|color|bgcolor|flood-color)=")([^"]*)(")',
                       lambda m: m.group(1) + colours(m.group(2), 'attr') + m.group(3), p)
            res.append(p)
    return ''.join(res)

out = transform(v3)

# ---------------------------------------------------------------- 3 verify
def fingerprint(doc):
    body = doc[doc.index('<body'):]
    body = re.sub(r'<(style|script)\b.*?</\1>', ' ', body, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', body)
    text = ' '.join(html.unescape(text).split())
    attrs = re.findall(r'\s(id|href|data-[\w-]+|aria-label|title|alt)="([^"]*)"', body)
    return text, attrs

base = git_show(BASE, 'v3.html')
# 1) everything apart from the intended home-page edits is unchanged
if fingerprint(home_layout(base)) != fingerprint(out):
    sys.exit('ABORT: visible text / ids / links changed')
# 2) the manual itself (every chapter) is untouched, independent of step 0
chap = lambda d: fingerprint('<body>' + d[d.index('<!-- CHAPTERS'):])
if chap(base) != chap(out):
    sys.exit('ABORT: chapter content changed')
toc = lambda d: re.search(r'<script id="jx-toc">(.*?)</script>', d, re.S).group(1)
if toc(out) != toc(git_show(BASE, 'v3.html')):
    sys.exit('ABORT: TOC changed')
def chromatic(x):
    x = ''.join(c * 2 for c in x) if len(x) == 3 else x
    v = [int(x[i:i + 2], 16) for i in (0, 2, 4)]
    return max(v) - min(v) > 2
left = [m.group(0) for m in HEX.finditer(re.sub(r'data:[^"\')\s]+', '', out)) if chromatic(m.group(1))]
OUT.write_text(out)
print('wrote', OUT.name, len(out), 'bytes; chapters, TOC and all non-home text identical to', BASE)
for k, v in log.items():
    print(f'  {k}: {len(v)} colours greyed')
print('  chromatic hex left anywhere (incl. selectors/text):', sorted(set(left))[:20])
