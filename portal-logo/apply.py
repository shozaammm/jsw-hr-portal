#!/usr/bin/env python3
"""Apply the official JSW Motors 2D-mark lockups and CSS-only list infographics to v2.html.

Source of the marks: ~/Desktop/Work/JSW MOTORS LOGO/JSW Motors 2dmark Logo pdf.pdf
(the brand sheet: horizontal / stacked / emblem lockups, black on white and white on black).
Vectors were extracted 1:1 into portal-logo/svg/*.svg (fill = currentColor).

Rules followed:
  * lockups are used unaltered (no stretch, rotate, effects, opacity) in solid black on
    light grounds and solid white on the dark hero, with clear space around them;
  * infographics only add a class to existing <ul> lists - every word stays verbatim.
    The script aborts if the tag-stripped text of any chapter changes.

Rerunnable: previous injections (marked) are stripped first.
"""
import re, sys, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = ROOT / 'portal-logo' / 'svg'
TARGETS = [ROOT / 'v2.html']


def sym(name, sid):
    s = (SVG / f'{name}.svg').read_text()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    inner = re.search(r'<svg[^>]*>(.*)</svg>', s, re.S).group(1)
    return vb, f'<symbol id="{sid}" viewBox="{vb}">{inner}</symbol>'


VB_H, SYM_H = sym('horizontal', 'jsw-mark-h')
VB_E, SYM_E = sym('emblem', 'jsw-mark-e')
_, SYM_S = sym('stacked', 'jsw-mark-s')
SPRITE = ('<!--jsw-logo-sprite--><svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">'
          + SYM_H + SYM_E + SYM_S + '</svg><!--/jsw-logo-sprite-->')


def use(sid, vb, cls):
    return f'<svg class="{cls}" viewBox="{vb}" role="img" aria-label="JSW Motors"><use href="#{sid}"/></svg>'


emb = (SVG / 'emblem.svg').read_text().replace('currentColor', '#000')
FAVICON = ('<!--jsw-favicon--><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'
           + re.sub(r'[<>#"%\s]', lambda m: {'<': '%3C', '>': '%3E', '#': '%23', '"': "'", '%': '%25'}.get(m.group(0), ' '), emb)
           + '"><!--/jsw-favicon-->')

LOGO_CSS = r'''
<style id="jx-logo-css">
/* Official JSW Motors 2D mark. Solid black on light grounds, solid white on dark. Never stretched. */
.jx-logo{display:block;height:var(--lh,18px);width:auto;aspect-ratio:var(--la);flex:0 0 auto;color:#000;fill:currentColor;stroke:none}
.jx-logo-h{--la:135.9/18.5}
.jx-logo-e{--la:33.4/23.4}
.jx-nav-brand{gap:14px}
.jx-nav-brand .jx-logo-h{--lh:15px}
.jx-nav-brand span{padding-left:14px;border-left:1px solid var(--jx-line-2);font-size:11.5px;letter-spacing:.14em;color:var(--jx-muted)}
.jx-top-brand{align-items:center;padding:6px 4px}
.jx-top-brand .jx-logo-h{--lh:15px}
.jx-top-brand .jx-logo-e{--lh:22px;display:none}
@media (max-width:1023px){
  .jx-top-brand .jx-logo-h{display:none}
  .jx-top-brand .jx-logo-e{display:block}
}
.jx-hero-brand{display:flex;align-items:center;margin:0 0 clamp(28px,5vw,56px)}
.jx-hero-brand .jx-logo{color:#fff;--lh:clamp(20px,2.6vw,28px)}
.jx-foot{display:flex;flex-direction:column;align-items:center;gap:14px}
.jx-foot .jx-logo-h{--lh:14px}
</style>
'''

# ---------------------------------------------------------------- infographics
# (anchor = exact text that begins the first <li>, class)
LISTS = [
    ('<li><strong>ILT</strong>', 'ix-quad'),                        # ch6 types of training
    ('<li>daily morning meeting - conducted', 'ix-cadence'),        # ch7 governance rhythm
    ('<li>Physical contact or advances', 'ix-hex'),                 # ch10 POSH - what counts
    ('<li>Display the names and contact details of the IC', 'ix-check'),  # ch10 POSH - dealership must do
    ('<li>Reason for leaving', 'ix-bubble'),                        # ch11 exit interview
    ('<li>Salary dues must be settled within', 'ix-receipt'),       # ch11 F&F settlement
    ('<li>Inform the reporting manager before the day starts', 'ix-stairs'),  # ch12 absence
    ('<li>Get written approval before travelling', 'ix-chevron'),  # ch12 how to claim
    ('<li>Travel by the cheapest sensible option', 'ix-ticket'),   # ch12 travel rules
    ('<li>New employees receive 2 sets', 'ix-tag'),                 # ch12 uniform policy
]

IX_CSS = r'''
<style id="jx-ix-css">
/* CSS-only infographic treatments for existing lists. Text is untouched. */
#jxView ul.ix{list-style:none;margin:18px 0 22px;padding:0;max-width:100%;counter-reset:ix}#jxView ul.ix > li{counter-increment:ix;position:relative;padding-left:0;color:var(--grey-700);font-size:14.5px;line-height:1.55;max-width:none}#jxView ul.ix > li::before,#jxView ul.ix > li::after{content:none;background:none;width:auto;height:auto;border-radius:0;top:auto;left:auto;font-size:inherit;line-height:inherit;color:inherit}

/* 1 quad - four shaped tiles on a dot grid */
#jxView ul.ix-quad{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}#jxView ul.ix-quad > li{padding:22px 22px 20px 22px;min-height:128px;border:1px solid var(--line-200);border-radius:16px;
  background:radial-gradient(circle at 1px 1px,rgba(17,17,19,.13) 1px,transparent 1.4px) 0 0/14px 14px,#fff;overflow:hidden}#jxView ul.ix-quad > li strong{display:block;font-size:26px;letter-spacing:-.02em;line-height:1;color:var(--ink);margin-bottom:10px;padding-right:56px}#jxView ul.ix-quad > li::after{content:"";position:absolute;top:18px;right:18px;width:40px;height:40px;background:var(--ink)}#jxView ul.ix-quad > li:nth-child(1)::after{border-radius:50%}#jxView ul.ix-quad > li:nth-child(2)::after{border-radius:8px;transform:rotate(12deg)}#jxView ul.ix-quad > li:nth-child(3)::after{clip-path:polygon(50% 4%,100% 96%,0 96%)}#jxView ul.ix-quad > li:nth-child(4)::after{background:none;border:3px solid var(--ink);border-radius:50%;
  box-shadow:inset 0 0 0 7px #fff,inset 0 0 0 10px var(--ink)}

/* 2 cadence - dot density shows meeting frequency */
#jxView ul.ix-cadence{display:grid;gap:0;border-top:1px solid var(--line-200)}#jxView ul.ix-cadence > li{padding:14px 38% 14px 0;border-bottom:1px solid var(--line-200)}#jxView ul.ix-cadence > li::after{content:"";position:absolute;right:0;top:50%;margin-top:-6px;width:calc(38% - 24px);height:12px;border-radius:6px;background-repeat:repeat-x;background-position:left center;
  background-image:radial-gradient(circle,var(--ink) 4px,transparent 4.6px)}#jxView ul.ix-cadence > li:nth-child(1)::after{background-size:12px 12px}#jxView ul.ix-cadence > li:nth-child(2)::after{background-size:30px 12px}#jxView ul.ix-cadence > li:nth-child(3)::after{background-size:60px 12px}#jxView ul.ix-cadence > li:nth-child(4)::after{background-size:120px 12px}
/* 3 hex - elongated hexagons */
#jxView ul.ix-hex{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}#jxView ul.ix-hex > li{padding:16px 34px;min-height:64px;color:#fff !important;background:var(--ink);
  clip-path:polygon(20px 0,calc(100% - 20px) 0,100% 50%,calc(100% - 20px) 100%,20px 100%,0 50%)}#jxView ul.ix-hex > li:nth-child(even){background:var(--grey-700)}#jxView ul.ix-hex > li:last-child:nth-child(odd){grid-column:1/-1}

/* 4 check - checklist badges */
#jxView ul.ix-check{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}#jxView ul.ix-check > li{padding:14px 16px 14px 56px;border:1px dashed var(--grey-300);border-radius:12px;background:#fff}#jxView ul.ix-check > li::before{content:"";position:absolute;left:14px;top:14px;width:28px;height:28px;border-radius:50%;background:var(--ink);}#jxView ul.ix-check > li::after{content:"";position:absolute;left:24px;top:19px;width:7px;height:13px;border:solid #fff;border-width:0 2.5px 2.5px 0;transform:rotate(45deg)}

/* 5 bubble - conversation prompts */
#jxView ul.ix-bubble{display:flex;flex-direction:column;gap:12px}#jxView ul.ix-bubble > li{align-self:flex-start;max-width:min(78%,560px);padding:12px 18px;border-radius:18px 18px 18px 4px;background:#fff;border:1px solid var(--line-200)}#jxView ul.ix-bubble > li:nth-child(even){align-self:flex-end;border-radius:18px 18px 4px 18px;background:var(--ink);border-color:var(--ink);color:#fff}

/* 6 receipt - torn-edge settlement slip */
#jxView ul.ix-receipt{max-width:620px;padding:22px 24px;background:#fff;border:1px solid var(--line-200);border-width:0 1px;position:relative;
  margin-top:28px;margin-bottom:32px}
#jxView ul.ix-receipt::before,#jxView ul.ix-receipt::after{content:"";position:absolute;left:0;right:0;height:9px;background-size:16px 9px;background-repeat:repeat-x}
#jxView ul.ix-receipt::before{top:-9px;background-image:linear-gradient(45deg,#fff 50%,transparent 50%),linear-gradient(-45deg,#fff 50%,transparent 50%);background-position:bottom left}
#jxView ul.ix-receipt::after{bottom:-9px;background-image:linear-gradient(135deg,#fff 50%,transparent 50%),linear-gradient(-135deg,#fff 50%,transparent 50%);background-position:top left}#jxView ul.ix-receipt > li{padding:11px 0 11px 44px;border-bottom:1px dashed var(--grey-300)}#jxView ul.ix-receipt > li:last-child{border-bottom:0}#jxView ul.ix-receipt > li::before{content:counter(ix,decimal-leading-zero);position:absolute;left:0;top:14px;font-family:var(--font-mono);font-size:12px;line-height:1.4;color:var(--grey-500)}

/* 7 stairs - escalation steps */
#jxView ul.ix-stairs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;align-items:end}#jxView ul.ix-stairs > li{padding:44px 14px 16px;border-radius:12px 12px 0 0;font-size:13.5px}#jxView ul.ix-stairs > li::before{content:counter(ix);position:absolute;top:12px;left:14px;font-weight:800;font-size:20px;line-height:1}#jxView ul.ix-stairs > li:nth-child(1){min-height:150px;background:#EDEDED}#jxView ul.ix-stairs > li:nth-child(2){min-height:185px;background:#D6D6D6}#jxView ul.ix-stairs > li:nth-child(3){min-height:220px;background:#5A5A5A;color:#fff}#jxView ul.ix-stairs > li:nth-child(4){min-height:255px;background:var(--ink);color:#fff}

/* 8 chevron - sequential claim steps */
#jxView ul.ix-chevron{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px 4px}#jxView ul.ix-chevron > li{padding:44px 34px 18px 26px;min-height:150px;background:#fff;
  clip-path:polygon(0 0,calc(100% - 18px) 0,100% 50%,calc(100% - 18px) 100%,0 100%,18px 50%);
  box-shadow:inset 0 0 0 1px var(--line-200)}#jxView ul.ix-chevron > li:nth-child(1),#jxView ul.ix-chevron > li:nth-child(4){clip-path:polygon(0 0,calc(100% - 18px) 0,100% 50%,calc(100% - 18px) 100%,0 100%)}#jxView ul.ix-chevron > li:nth-child(odd){background:#F1F1F0}#jxView ul.ix-chevron > li::before{content:counter(ix,decimal-leading-zero);position:absolute;top:14px;left:26px;font-family:var(--font-mono);font-size:13px;font-weight:700;color:var(--ink)}

/* 9 ticket - perforated stubs */
#jxView ul.ix-ticket{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}#jxView ul.ix-ticket > li{padding:16px 18px 16px 70px;min-height:72px;
  background:radial-gradient(circle at 0 50%,transparent 9px,#fff 9.5px) left/51% 100% no-repeat,
             radial-gradient(circle at 100% 50%,transparent 9px,#fff 9.5px) right/51% 100% no-repeat;
  filter:drop-shadow(0 0 .5px rgba(0,0,0,.45))}#jxView ul.ix-ticket > li::before{content:counter(ix);position:absolute;left:0;top:0;bottom:0;width:52px;display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:18px;color:var(--ink);border-right:2px dotted var(--grey-300)}

/* 10 tag - hang-tags with eyelets */
#jxView ul.ix-tag{display:flex;flex-direction:row !important;flex-wrap:wrap;gap:14px}#jxView ul.ix-tag > li{flex:1 1 180px;padding:40px 18px 18px;background:#fff;border:1px solid var(--line-200);
  border-radius:4px 4px 14px 14px;clip-path:polygon(22% 0,78% 0,100% 18px,100% 100%,0 100%,0 18px)}#jxView ul.ix-tag > li::before{content:"";position:absolute;top:12px;left:50%;width:12px;height:12px;margin-left:-6px;border-radius:50%;border:2px solid var(--ink);background:var(--jx-bg,#E7E7E7)}

@media (max-width:640px){#jxView ul.ix-quad,#jxView ul.ix-hex,#jxView ul.ix-check,#jxView ul.ix-ticket,#jxView ul.ix-chevron{grid-template-columns:1fr}#jxView ul.ix-chevron > li{clip-path:polygon(0 0,100% 0,100% calc(100% - 14px),50% 100%,0 calc(100% - 14px));min-height:0;padding:40px 18px 28px}#jxView ul.ix-chevron > li:nth-child(n){clip-path:polygon(0 0,100% 0,100% calc(100% - 14px),50% 100%,0 calc(100% - 14px))}#jxView ul.ix-stairs{grid-template-columns:1fr;align-items:stretch}#jxView ul.ix-stairs > li{min-height:0 !important;padding:14px 14px 14px 48px;border-radius:10px}#jxView ul.ix-stairs > li:nth-child(1){margin-right:24px}#jxView ul.ix-stairs > li:nth-child(2){margin-right:16px}#jxView ul.ix-stairs > li:nth-child(3){margin-right:8px}#jxView ul.ix-stairs > li::before{top:14px}#jxView ul.ix-bubble > li{max-width:90%}#jxView ul.ix-tag > li{flex:1 1 100%}#jxView ul.ix-cadence > li{padding:12px 0 34px}#jxView ul.ix-cadence > li::after{top:auto;bottom:12px;margin-top:0;left:0;right:auto;width:100%}
}
#jxView ul.ix-hex > li *,#jxView ul.ix-bubble > li:nth-child(even),#jxView ul.ix-bubble > li:nth-child(even) *,
#jxView ul.ix-stairs > li:nth-child(n+3),#jxView ul.ix-stairs > li:nth-child(n+3) *{color:#fff !important}
</style>
'''


def chapter_text(s):
    a = s.find('<article class="jx-chapter"')
    b = s.find('</main>', a)
    t = re.sub(r'<style.*?</style>|<script.*?</script>|<!--.*?-->', '', s[a:b], flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def strip_previous(s):
    s = re.sub(r'<!--jsw-logo-sprite-->.*?<!--/jsw-logo-sprite-->', '', s, flags=re.S)
    s = re.sub(r'<!--jsw-favicon-->.*?<!--/jsw-favicon-->', '', s, flags=re.S)
    s = re.sub(r'\n?<style id="jx-logo-css">.*?</style>\n?', '', s, flags=re.S)
    s = re.sub(r'\n?<style id="jx-ix-css">.*?</style>\n?', '', s, flags=re.S)
    s = re.sub(r'<svg class="jx-logo[^"]*"[^>]*><use href="#jsw-mark-[hes]"/></svg>', '', s)
    s = re.sub(r'<div class="jx-hero-brand">\s*</div>', '', s)
    s = re.sub(r'<ul class="list-clean ix ix-[a-z]+">', '<ul class="list-clean">', s)
    return s


def apply(s):
    before = chapter_text(s)
    s = strip_previous(s)

    # head: favicon + css
    s = s.replace('</title>', '</title>' + FAVICON, 1)
    i = s.find('</head>')
    s = s[:i] + LOGO_CSS + IX_CSS + s[i:]
    # sprite right after <body ...>
    m = re.search(r'<body[^>]*>', s)
    s = s[:m.end()] + SPRITE + s[m.end():]

    def sub1(pat, rep):
        nonlocal s
        s2, n = re.subn(pat, rep, s, count=1, flags=re.S)
        assert n == 1, pat
        s = s2

    # top bar (desktop with collapsed sidebar: horizontal; phone: emblem)
    sub1(r'(<button class="jx-top-brand"[^>]*>)\s*(</button>)',
         r'\1' + use('jsw-mark-h', VB_H, 'jx-logo jx-logo-h') + use('jsw-mark-e', VB_E, 'jx-logo jx-logo-e') + r'\2')
    # sidebar head: horizontal lockup | HROS
    sub1(r'(<button class="jx-nav-brand"[^>]*>)(\s*<span>HROS</span>)',
         r'\1' + use('jsw-mark-h', VB_H, 'jx-logo jx-logo-h') + r'\2')
    # hero: white horizontal lockup above the title
    sub1(r'(<div class="jx-hero-glow" aria-hidden="true"></div>)',
         r'\1<div class="jx-hero-brand">' + use('jsw-mark-h', VB_H, 'jx-logo jx-logo-h') + '</div>')
    # home footer
    sub1(r'(<footer class="jx-foot">)', r'\1' + use('jsw-mark-h', VB_H, 'jx-logo jx-logo-h'))

    for anchor, cls in LISTS:
        assert s.count(anchor) == 1, anchor
        i = s.find(anchor)
        j = s.rfind('<ul class="list-clean">', 0, i)
        assert j != -1 and s[j:i].strip().endswith('>') and s[j:i].count('<li') == 0, anchor
        s = s[:j] + f'<ul class="list-clean ix {cls}">' + s[j + len('<ul class="list-clean">'):]

    after = chapter_text(s)
    if before != after:
        import difflib
        for l in list(difflib.unified_diff(before.split(' '), after.split(' '), lineterm='', n=3))[:40]:
            print(l)
        sys.exit('ABORT: chapter text changed')
    return s


if __name__ == '__main__':
    for p in TARGETS:
        s = p.read_text(encoding='utf-8')
        out = apply(s)
        p.write_text(out, encoding='utf-8')
        print(p.name, 'ok', len(s), '->', len(out))
