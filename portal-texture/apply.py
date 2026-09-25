#!/usr/bin/env python3
"""Grain textures for the three portal samples (assets in portal-texture/assets).

v1  cover photo, part banners and chapter-head photos become textures; the three
    intro heads (which had no photo) get one too. The contents strip, the three
    intro-section images and the role-directory avatars keep their original photos.
v2  the light texture is the page ground; the white reading sheet is removed so
    text sits on it, while the manual's cards, tables and panels keep their own
    surfaces. Dark grain in the hero.
v3  same page ground; its cards, tables and panels get their surfaces back.

Everything is injected as <style id="jx-grain"> plus a few CSS-variable swaps.
Always starts from the pre-texture commit (e0ec76a), so it is safe to rerun.
Aborts if visible text, element ids, or any photo that must be kept changes.

    python3 portal-texture/apply.py
"""
import base64, hashlib, html, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).resolve().parent / "assets"
BASE_REV = sys.argv[1] if len(sys.argv) > 1 else "e0ec76a"  # last commit before the textures

TARGETS = {  # source (read from git) -> outputs kept byte-identical
    "v1.html": ["v1.html", "index.html"],
    "v2.html": ["v2.html", "hr-manual-2.html", "jsw-hr-portal-v2.html"],
    "v3.html": ["v3.html"],
}


def uri(name):
    return "data:image/jpeg;base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()


DATA_JPEG = re.compile(r'url\(\s*["\']?data:image/jpeg;base64,[A-Za-z0-9+/=\s]+["\']?\s*\)')


def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def inject(s, css):
    assert 'id="jx-grain"' not in s
    i = s.index("</head>")
    return s[:i] + '\n<style id="jx-grain">' + css + "</style>\n" + s[i:]


def tex_vars():
    return ':root{--tx-a:url("%s");--tx-b:url("%s");--tx-c:url("%s")}\n' % (
        uri("grain-a.jpg"), uri("grain-b.jpg"), uri("grain-c.jpg"))


# ---------------------------------------------------------------- v1
V1_CSS = """
/* Textures are already greyscale: skip the per-frame filter pass on these large layers. */
html body .cover-photo, html body .section-banner, html body .section-banner .banner-photo, html body .ch-thumb{filter:none !important}

/* The three intro heads (Foreword, Vision, Role of HR) had no photo: give them the
   same right-hand texture as the chapter heads, drawn exactly like .ch-thumb. */
section.chap > .chap-head:not(:has(> .ch-thumb))::after{
  content:'';position:absolute;top:0;right:0;bottom:0;width:66%;max-width:720px;z-index:1;pointer-events:none;
  background:var(--tx-c) center 15% / cover no-repeat;
  -webkit-mask-image:linear-gradient(to right, transparent 0%, rgba(0,0,0,0.18) 18%, rgba(0,0,0,0.85) 55%, black 100%);
          mask-image:linear-gradient(to right, transparent 0%, rgba(0,0,0,0.18) 18%, rgba(0,0,0,0.85) 55%, black 100%)}
@media (max-width: 900px){
  section.chap > .chap-head:not(:has(> .ch-thumb))::after{width:100%;max-width:none;opacity:.22;
    -webkit-mask-image:linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.5) 40%, black 100%);
            mask-image:linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.5) 40%, black 100%)}
}
@media print{ section.chap > .chap-head::after{display:none !important} }

@media screen{
  /* Small grey kickers on the dark chapter heads and part banners: lift to >= 4.5:1. */
  html body section.chap .chap-head .chap-num, html body .section-banner .banner-kicker{color:#a8a8a8 !important}
}
@media screen and (max-width: 900px){
  /* Part-banner contents lines were nowrap and got clipped at the banner edge on phones. */
  html body .section-banner .banner-contents span{white-space:normal}
  /* Text spans the full banner width here, so the scrim must too (was fading to ~0 on the right). */
  html body .section-banner::after{background:linear-gradient(180deg, rgba(16,15,14,.90) 0%, rgba(16,15,14,.80) 100%)}
}
"""


def v1(s):
    counts = {"cover": 0, "banner": 0, "ch": 0}
    def repl(m):
        var = m.group(1)
        counts[var] += 1
        tex = {"cover": "var(--tx-a)",   # opening page: the darker texture
               "banner": "var(--tx-a)",  # full width: only the landscape texture stays crisp
               "ch": "var(--tx-c)"}[var] # uniformly dark: safe under white titles
        return f"--{var}-img:{tex}"
    s, _ = re.subn(r'--(cover|banner|ch)-img:\s*' + DATA_JPEG.pattern, repl, s)
    assert counts == {"cover": 1, "banner": 6, "ch": 11}, counts

    return inject(s, tex_vars() + V1_CSS + CAPTIONS)


# ---------------------------------------------------------------- v2 / v3
# The light texture is the whole page ground: one fixed layer behind everything,
# so it costs nothing while scrolling (no repaint, no background-attachment:fixed,
# which iOS ignores). A white wash keeps every text colour legible on its darkest part.
GROUND = """
@media screen{
  html{background:#E4E4E2}
  html body{background:transparent !important}
  html body::before{content:'';position:fixed;left:0;right:0;top:0;height:100vh;height:100lvh;z-index:-1;pointer-events:none;
    background:linear-gradient(rgba(244,244,242,.85), rgba(244,244,242,.85)), var(--tx-b) center / cover no-repeat;
    transform:translateZ(0)}
  /* desktop sidebar lets the ground through (the phone nav sheet stays solid: it covers text) */
  @media (min-width:1024px){ html body .jx-nav{background:rgba(242,242,240,.72)} }
  /* Grey text tokens were tuned for white; on the textured ground they need a
     step darker to stay >= 4.5:1 at its darkest point. */
  html body .jx-main{--grey-400:#545454;--grey-500:#545454;--jx-muted:#505050;--g-7:#505050}
  /* Pager "Next" labels on the black button (was 3.9:1). */
  html body .jx-pager-next .jx-pager-k, html body .jx-pager-next .jx-pager-t b{color:#a3a3a3}
}
"""

V2_CSS = """
/* Home hero: dark grain under a dark wash, heavier on the text side.
   The TRUST ghost letters (and pillar initials) were ~1.4:1; lift to >= 3:1 large-text. */
.jx-hero{--jx-trust:#787878}
.jx-hero{background:linear-gradient(100deg, rgba(14,14,14,.90) 0%, rgba(14,14,14,.78) 55%, rgba(14,14,14,.58) 100%), var(--tx-a) center / cover no-repeat, var(--jx-ink)}
@media (max-width: 700px){
  .jx-hero{background:linear-gradient(180deg, rgba(14,14,14,.88), rgba(14,14,14,.74)), var(--tx-c) center 30% / cover no-repeat, var(--jx-ink)}
}
.jx-resume-icon{background:linear-gradient(rgba(14,14,14,.45), rgba(14,14,14,.45)), var(--tx-a) 70% 30% / 320px auto no-repeat, var(--jx-ink)}

@media screen{
/* Chapter: no white reading sheet — the manual reads straight off the ground.
   Its own cards, tables and panels keep their surfaces.
   Reset negative mobile margin so text stays aligned with .jx-head and doesn't touch phone edges. */
.jx-chapter{background:none;border:0;border-radius:0;box-shadow:none;margin:0;padding:0}
.jx-chapter section.chap,
.jx-chapter section.chap:nth-of-type(n){background:none !important;border:0 !important;border-radius:0 !important;box-shadow:none !important;
  margin:0 !important;padding:clamp(20px, 3vw, 36px) 0 8px !important}
.jx-head{padding-bottom:18px;border-bottom:1px solid rgba(27,27,27,.14)}
.jx-chapter section.chap .img-card, .jx-chapter section.chap figure{box-shadow:none}
}
@media (max-width:760px){
  .jx-chapter section.chap{margin:0 !important;padding:18px 0 8px !important}
  .jx-chapter [id]{scroll-margin-top:calc(var(--jx-top-h) + var(--jx-chips-h) + 24px) !important}
}
"""

V3_CSS = """
.jx-resume-icon{background:linear-gradient(rgba(14,14,14,.45), rgba(14,14,14,.45)), var(--tx-a) 70% 30% / 320px auto no-repeat, var(--g-11)}
"""

# v3's own stylesheet stripped the fill from the manual's cards, tables and panels.
# On the textured ground they keep their own surfaces instead (user, 2026-09-25).
V3_FLATTEN_START = "/* Text panels in the manual (step cards, month cards, info boxes, table"
V3_FLATTEN_END = ".jx-chapter section.chap tbody tr:nth-child(even) td{background:rgba(27,27,27,.03)}\n"


def v3_restore_surfaces(s):
    a = s.index(V3_FLATTEN_START)
    b = s.index(V3_FLATTEN_END, a) + len(V3_FLATTEN_END)
    assert s.count(V3_FLATTEN_START) == 1 and b - a < 3000
    return s[:a] + s[b:]


# Diagram captions set inline to #8A8A8A on white panels (3.45:1) -> #666 (5.7:1).
CAPTIONS = """
@media screen{ html body [style*="color:#8A8A8A"], html body [style*="color:#8a8a8a"]{color:#666 !important} }
"""


def jx(s, extra):
    return inject(s, tex_vars() + GROUND + CAPTIONS + extra)


# ---------------------------------------------------------------- checks
def visible_text(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def ids(s):
    return [i for i in re.findall(r'\bid="([^"]+)"', s) if i != "jx-grain"]


def kept(s):
    """Photos that must survive byte-for-byte: intro images, avatars, contents strip."""
    out = [md5(m.group(0)) for m in re.finditer(
        r'<img alt="(?:Leadership Commitment|JSW Vision (?:&amp;|&) Foundation|Strategic HR Practice)"[^>]*>', s)]
    out += [md5(m.group(0)) for m in re.finditer(r'<img\b[^>]*\brd-avatar-(?:sm|lg)\b[^>]*>', s)]
    out += [md5(m.group(0)) for m in re.finditer(r'--hi-img:\s*' + DATA_JPEG.pattern, s)]
    return out


def main():
    for src, outs in TARGETS.items():
        before = subprocess.run(["git", "show", f"{BASE_REV}:{src}"], cwd=ROOT,
                                capture_output=True, check=True).stdout.decode("utf-8")
        if src == "v1.html":
            s = v1(before)
        elif src == "v2.html":
            s = jx(before, V2_CSS)
        else:
            s = jx(v3_restore_surfaces(before), V3_CSS)

        assert visible_text(s) == visible_text(before), f"{src}: visible text changed"
        assert ids(s) == ids(before), f"{src}: ids changed"
        assert kept(s) == kept(before) and len(kept(s)) >= 70, f"{src}: kept photos changed"
        for o in outs:
            (ROOT / o).write_text(s, encoding="utf-8")
        print(f"{src}: {len(before)//1024}KB -> {len(s)//1024}KB, kept photos {len(kept(s))} "
              f"-> {', '.join(outs)}")


if __name__ == "__main__":
    main()
