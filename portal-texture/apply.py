#!/usr/bin/env python3
"""Swap the portal photography for the grain textures in portal-texture/assets.

Kept as-is: the v1 cover photo and the Foreword ("Leadership Commitment") image.
Every other photo (v1 banners, chapter thumbs, contents strip, the two other
intro cards, and all role-directory avatars in v1/v2/v3) becomes a texture.
v2 and v3 also get the textures as backgrounds via <style id="jx-grain">.

Always starts from the pre-texture commit (e0ec76a), so it is safe to rerun.
Aborts if visible text, element ids, or the two kept images change.

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
N_AVATARS = 9


def uri(name):
    return "data:image/jpeg;base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()


DATA_JPEG = re.compile(r'url\(\s*["\']?data:image/jpeg;base64,[A-Za-z0-9+/=\s]+["\']?\s*\)')
IMG_SRC = re.compile(r'src="data:image/jpeg;base64,[A-Za-z0-9+/=\s]+"')


def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


# ---------------------------------------------------------------- avatars
def swap_avatars(s):
    """Each role gets one texture crop, the same in its list button and detail card."""
    def av(role):
        return f'src="{uri(f"av{int(role) % N_AVATARS}.jpg")}"'

    out, pos, n = [], 0, 0
    for m in re.finditer(r'<img\b[^>]*\brd-avatar-(?:sm|lg)\b[^>]*>', s):
        tag = m.group(0)
        before = s[:m.start()]
        if "rd-avatar-sm" in tag:
            role = re.findall(r'data-role="(\d+)"', before[-400:])[-1]
        else:
            host = re.findall(r'id="(rd-role-\d+|rdDetail)"', before[-600:])[-1]
            role = "0" if host == "rdDetail" else host.split("-")[-1]
        new, k = IMG_SRC.subn(av(role), tag)
        assert k == 1, tag[:120]
        out += [s[pos:m.start()], new]
        pos, n = m.end(), n + 1
    out.append(s[pos:])
    return "".join(out), n


# ---------------------------------------------------------------- v1
def swap_img_by_alt(s, alt, asset):
    m = re.search(r'<img alt="%s"[^>]*>' % re.escape(alt), s)
    new, k = IMG_SRC.subn(f'src="{uri(asset)}"', m.group(0))
    assert k == 1, alt
    return s[:m.start()] + new + s[m.end():]


def v1(s):
    # CSS-variable photos, in document order: banners, chapter thumbs, contents strip.
    counts = {"banner": 0, "ch": 0, "hi": 0}
    def repl(m):
        var = m.group(1)
        if var == "cover":
            return m.group(0)                            # opening page: keep
        key = var.split("-")[0]
        i = counts[key]; counts[key] += 1
        if key == "banner":                              # full-width: only the landscape texture stays crisp
            tex = "var(--tx-a)"
        elif key == "ch":                                # uniformly dark: safe under white titles
            tex = "var(--tx-c)"
        else:                                            # contents strip carries no text
            tex = "var(--tx-b)"
        return f"--{var}-img:{tex}"
    s, _ = re.subn(r'--(cover|banner|ch|hi)-img:\s*' + DATA_JPEG.pattern, repl, s)
    assert counts == {"banner": 6, "ch": 11, "hi": 1}, counts

    s = swap_img_by_alt(s, "JSW Vision &amp; Foundation" if "JSW Vision &amp; Foundation" in s
                        else "JSW Vision & Foundation", "card-b.jpg")
    s = swap_img_by_alt(s, "Strategic HR Practice", "card-c.jpg")

    css = f"""
<style id="jx-grain">
:root{{--tx-a:url("{uri('grain-a.jpg')}");--tx-b:url("{uri('grain-b.jpg')}");--tx-c:url("{uri('grain-c.jpg')}")}}
/* Textures are already greyscale: skip the per-frame filter pass on these large layers. */
html body .section-banner, html body .section-banner .banner-photo, html body .ch-thumb, html body .hi-strip, html body .hi-strip::before{{filter:none !important}}
@media screen{{
  /* Small grey kickers on the dark chapter heads and part banners: lift to >= 4.5:1. */
  html body section.chap .chap-head .chap-num, html body .section-banner .banner-kicker{{color:#a8a8a8 !important}}
}}
@media screen and (max-width: 900px){{
  /* Part-banner contents lines were nowrap and got clipped at the banner edge on phones. */
  html body .section-banner .banner-contents span{{white-space:normal}}
  /* Text spans the full banner width here, so the scrim must too (was fading to ~0 on the right). */
  html body .section-banner::after{{background:linear-gradient(180deg, rgba(16,15,14,.90) 0%, rgba(16,15,14,.80) 100%)}}
}}
</style>
"""
    return inject(s, css)


# ---------------------------------------------------------------- v2 / v3
SHARED_JX = """
:root{--tx-a:url("%(a)s");--tx-b:url("%(b)s");--tx-c:url("%(c)s")}
/* Chapter heading band: the light diagonal texture under a white wash, fading
   into the page so the dark heading text keeps its contrast. */
.jx-head{position:relative;isolation:isolate}
.jx-head::before{content:'';position:absolute;z-index:-1;pointer-events:none;
  inset:calc(-1 * clamp(20px, 3vw, 40px)) calc(-1 * clamp(16px, 3vw, 48px)) 0;
  background:linear-gradient(180deg, rgba(255,255,255,.72), rgba(255,255,255,.86)), var(--tx-b) left 22%% / cover no-repeat;
  -webkit-mask-image:linear-gradient(180deg, #000 55%%, transparent);
          mask-image:linear-gradient(180deg, #000 55%%, transparent)}
"""

V2_CSS = """
/* Home hero: dark grain under a dark wash, heavier on the text side.
   The TRUST ghost letters (and pillar initials) were ~1.4:1; lift to >= 3:1 large-text. */
.jx-hero{--jx-trust:#787878}
.jx-hero{background:linear-gradient(100deg, rgba(14,14,14,.90) 0%%, rgba(14,14,14,.78) 55%%, rgba(14,14,14,.58) 100%%), var(--tx-a) center / cover no-repeat, var(--jx-ink)}
@media (max-width: 700px){
  .jx-hero{background:linear-gradient(180deg, rgba(14,14,14,.88), rgba(14,14,14,.74)), var(--tx-c) center 30%% / cover no-repeat, var(--jx-ink)}
}
.jx-resume-icon{background:linear-gradient(rgba(14,14,14,.45), rgba(14,14,14,.45)), var(--tx-a) 70%% 30%% / 320px auto no-repeat, var(--jx-ink)}
"""

V3_CSS = """
/* Home title band: same treatment as the chapter headings. */
.jx-home-title{position:relative;isolation:isolate;padding-top:clamp(18px, 2.4vw, 28px)}
.jx-home-title::before{content:'';position:absolute;z-index:-1;pointer-events:none;
  inset:calc(-1 * clamp(20px, 3vw, 40px)) calc(-1 * clamp(16px, 3vw, 48px)) 0;
  background:linear-gradient(180deg, rgba(255,255,255,.72), rgba(255,255,255,.86)), var(--tx-b) left 18%% / cover no-repeat;
  -webkit-mask-image:linear-gradient(180deg, #000 55%%, transparent);
          mask-image:linear-gradient(180deg, #000 55%%, transparent)}
.jx-resume-icon{background:linear-gradient(rgba(14,14,14,.45), rgba(14,14,14,.45)), var(--tx-a) 70%% 30%% / 320px auto no-repeat, var(--g-11)}
"""


def jx(s, extra):
    vals = {"a": uri("grain-a.jpg"), "b": uri("grain-b.jpg"), "c": uri("grain-c.jpg")}
    css = '\n<style id="jx-grain">' + (SHARED_JX + extra) % vals + "</style>\n"
    return inject(s, css)


def inject(s, css):
    assert 'id="jx-grain"' not in s
    i = s.index("</head>")
    return s[:i] + css + s[i:]


# ---------------------------------------------------------------- checks
def visible_text(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def ids(s):
    return [i for i in re.findall(r'\bid="([^"]+)"', s) if i != "jx-grain"]


def kept(s):
    out = [md5(m.group(0)) for m in re.finditer(r'<img alt="Leadership Commitment"[^>]*>', s)]
    out += [md5(m.group(0)) for m in re.finditer(r'--cover-img:\s*' + DATA_JPEG.pattern, s)]
    return out


def main():
    for src, outs in TARGETS.items():
        before = subprocess.run(["git", "show", f"{BASE_REV}:{src}"], cwd=ROOT,
                                capture_output=True, check=True).stdout.decode("utf-8")
        s, n_av = swap_avatars(before)
        s = v1(s) if src == "v1.html" else jx(s, V2_CSS if src == "v2.html" else V3_CSS)

        assert visible_text(s) == visible_text(before), f"{src}: visible text changed"
        assert ids(s) == ids(before), f"{src}: ids changed"
        assert kept(s) == kept(before) and kept(s), f"{src}: kept images changed"
        left = len(re.findall(r"data:image/jpeg", s)) - len(kept(s))
        for o in outs:
            (ROOT / o).write_text(s, encoding="utf-8")
        print(f"{src}: {n_av} avatars, {len(before)//1024}KB -> {len(s)//1024}KB, "
              f"jpeg uris besides kept: {left} -> {', '.join(outs)}")


if __name__ == "__main__":
    main()
