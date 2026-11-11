#!/usr/bin/env python3
"""Official JSW Motors 2D-mark lockups + contextual list infographics for v2.html.

Marks: ~/Desktop/Work/JSW MOTORS LOGO/JSW Motors 2dmark Logo pdf.pdf (brand sheet:
horizontal / stacked / emblem, black on white and white on black), extracted 1:1 into
portal-logo/svg/*.svg. Used unaltered: solid black on light, solid white on dark, no
opacity, stretch or effects.

Infographics: each target list keeps every word of the manual. The script only
  * wraps each item's original HTML in <span class="ix-txt">,
  * adds an aria-hidden icon / calendar that depicts what the item says,
  * (meetings only) wraps the meeting name, which is already the item's first words, in <strong>.
No new words are introduced. The script aborts if the tag-stripped chapter text changes.

Rerunnable: each transformed list carries its original markup (base64) in a comment and
is restored before re-applying.
"""
import re, sys, html, base64, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = ROOT / 'portal-logo' / 'svg'
TARGETS = [ROOT / 'v2.html']


# ------------------------------------------------------------------ logo
def sym(name, sid):
    s = (SVG / f'{name}.svg').read_text()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    inner = re.search(r'<svg[^>]*>(.*)</svg>', s, re.S).group(1)
    return vb, f'<symbol id="{sid}" viewBox="{vb}">{inner}</symbol>'


VB_H, SYM_H = sym('horizontal', 'jsw-mark-h')
VB_E, SYM_E = sym('emblem', 'jsw-mark-e')
SPRITE = ('<!--jsw-logo-sprite--><svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">'
          + SYM_H + SYM_E + '</svg><!--/jsw-logo-sprite-->')


def use(sid, vb, cls, label=True):
    a = 'role="img" aria-label="JSW Motors"' if label else 'aria-hidden="true" focusable="false"'
    return f'<svg class="{cls}" viewBox="{vb}" {a}><use href="#{sid}"/></svg>'


H = lambda cls='', label=True: use('jsw-mark-h', VB_H, ('jx-logo jx-logo-h ' + cls).strip(), label)
E = lambda cls='', label=True: use('jsw-mark-e', VB_E, ('jx-logo jx-logo-e ' + cls).strip(), label)

emb = (SVG / 'emblem.svg').read_text().replace('currentColor', '#000')
FAVICON = ('<!--jsw-favicon--><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'
           + re.sub(r'[<>#"%\s]', lambda m: {'<': '%3C', '>': '%3E', '#': '%23', '"': "'", '%': '%25'}.get(m.group(0), ' '), emb)
           + '"><!--/jsw-favicon-->')

LOGO_CSS = r'''
<style id="jx-logo-css">
/* Official JSW Motors 2D mark. Solid black on light grounds, solid white on dark. Never stretched or faded. */
.jx-logo{display:block;height:var(--lh,18px);width:auto;aspect-ratio:var(--la);flex:0 0 auto;color:#000;fill:currentColor;stroke:none}
.jx-logo-h{--la:135.9/18.5}
.jx-logo-e{--la:33.4/23.4}
/* sidebar */
.jx-nav-brand{gap:14px}
.jx-nav-brand .jx-logo-h{--lh:16px}
.jx-nav-brand span{padding-left:14px;border-left:1px solid var(--jx-line-2);font-size:11.5px;letter-spacing:.14em;color:var(--jx-muted)}
/* top bar: horizontal on desktop (sidebar collapsed), emblem on phone */
.jx-top-brand{align-items:center;padding:6px 4px}
.jx-top-brand .jx-logo-h{--lh:16px}
.jx-top-brand .jx-logo-e{--lh:24px;display:none}
@media (max-width:1023px){
  .jx-top-brand .jx-logo-h{display:none}
  .jx-top-brand .jx-logo-e{display:block}
}
/* home hero (dark) */
.jx-hero-brand{display:flex;align-items:center;margin:0 0 clamp(28px,5vw,56px)}
.jx-hero-brand .jx-logo{color:#fff;--lh:clamp(22px,3vw,34px)}
/* home footer */
.jx-foot{display:flex;flex-direction:column;align-items:center;gap:14px}
.jx-foot .jx-logo-h{--lh:16px}
/* chapter header: emblem sits opposite the chapter title */
.jx-head-row{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}
.jx-head-row > .jx-head-mark{--lh:30px;margin-top:6px}
@media (max-width:640px){ .jx-head-row > .jx-head-mark{--lh:22px;margin-top:4px} }
/* official viewers (org chart / annexures): white lockup on the dark header */
.annex-modal-header .jx-modal-mark{color:#fff;--lh:15px;margin-right:18px;padding-right:18px;box-sizing:content-box;border-right:1px solid rgba(255,255,255,.22);align-self:center}
@media (max-width:640px){ .annex-modal-header .jx-modal-mark{display:none} }
</style>
'''


# ------------------------------------------------------------------ icons (24px line icons)
I = {
 'present': '<path d="M2 3h20"/><path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/><path d="m7 21 5-5 5 5"/>',
 'laptop-play': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20"/><path d="M10.5 7.8 14 10l-3.5 2.2z"/>',
 'wrench': '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
 'refresh': '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M8 16H3v5"/>',
 'hand': '<path d="M18 11V6a2 2 0 0 0-4 0v5"/><path d="M14 10V4a2 2 0 0 0-4 0v6"/><path d="M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-6-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>',
 'msg-alert': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M12 7v4"/><path d="M12 14h.01"/>',
 'msg-dots': '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/><path d="M8 12h.01"/><path d="M12 12h.01"/><path d="M16 12h.01"/>',
 'monitor': '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
 'phone-img': '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/><path d="m8 13 2.5-3 2 2 1.5-1.5L16 13"/>',
 'board': '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
 'user-plus': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6"/><path d="M22 11h-6"/>',
 'cal-check': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/><path d="m9 16 2 2 4-4"/>',
 'cap': '<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
 'file-up': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="m9 15 3-3 3 3"/>',
 'mail': '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
 'logout': '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
 'users': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
 'building': '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M12 6h.01"/><path d="M16 6h.01"/><path d="M8 10h.01"/><path d="M12 10h.01"/><path d="M16 10h.01"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/>',
 'trend': '<path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>',
 'rupee': '<path d="M6 3h12"/><path d="M6 8h12"/><path d="m6 13 8.5 8"/><path d="M6 13h3a5 5 0 0 0 0-10"/>',
 'thumb': '<path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
 'msg-text': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M7 8h10"/><path d="M7 12h6"/>',
 'cash': '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01"/><path d="M18 12h.01"/>',
 'award': '<circle cx="12" cy="8" r="6"/><path d="M15.5 12.9 17 22l-5-3-5 3 1.5-9.1"/>',
 'bank': '<path d="M3 22h18"/><path d="M6 18v-7"/><path d="M10 18v-7"/><path d="M14 18v-7"/><path d="M18 18v-7"/><path d="M12 2 20 7H4z"/>',
 'trophy': '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
 'scale': '<path d="M12 3v18"/><path d="M7 21h10"/><path d="M3 7h18"/><path d="m6 7-3 7a3 3 0 0 0 6 0z"/><path d="m18 7-3 7a3 3 0 0 0 6 0z"/>',
 'file-check': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/>',
 'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
 'laptop-check': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20"/><path d="m9 10 2 2 4-4"/>',
 'alert': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
 'user-x': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m17 8 5 5"/><path d="m22 8-5 5"/>',
 'wallet': '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
 'receipt': '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6"/><path d="M16 12H8"/><path d="M13 16H8"/>',
 'send': '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
 'check-circle': '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
 'swap': '<path d="m8 3-4 4 4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
 'tag-down': '<path d="M12 2H2v10l9.29 9.29a1 1 0 0 0 1.41 0l8.59-8.59a1 1 0 0 0 0-1.41Z"/><path d="M7 7h.01"/>',
 'suitcase': '<rect x="4" y="7" width="16" height="13" rx="2"/><path d="M9 7V4h6v3"/><path d="M4 12h16"/><path d="M9 20v1"/><path d="M15 20v1"/>',
 'car': '<path d="M19 17h2v-4l-2.5-5h-13L3 13v4h2"/><circle cx="7.5" cy="17" r="2"/><circle cx="16.5" cy="17" r="2"/><path d="M9.5 17h5"/><path d="M3 13h18"/>',
 'clock': '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
 'shirt': '<path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/>',
 'bag': '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
 'drop': '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
 'ban': '<circle cx="12" cy="12" r="9"/><path d="m5.7 5.7 12.6 12.6"/>',
 'tick': '<path d="M20 6 9 17l-5-5"/>',
}


def ico(name, cls='ix-ico'):
    return f'<span class="{cls}" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false">{I[name]}</svg></span>'


# ------------------------------------------------------------------ list transforms
def items(ul):
    inner = re.search(r'<ul[^>]*>(.*)</ul>', ul, re.S).group(1)
    return [x.strip() for x in re.findall(r'<li>(.*?)</li>', inner, re.S)]


def build(cls, lis):
    return f'<ul class="ix {cls}">' + ''.join(f'<li>{x}</li>' for x in lis) + '</ul>'


def simple(cls, icons, badge=None):
    def f(its):
        assert len(its) == len(icons), (cls, len(its))
        out = []
        for t, ic in zip(its, icons):
            b = ico(badge, 'ix-badge') if badge else ''
            out.append(f'{ico(ic)}{b}<span class="ix-txt">{t}</span>')
        return build(cls, out)
    return f


def meetings(its):
    # daily / weekly / fortnightly / monthly: a 4-week calendar marks the days the meeting is held
    on = [set(range(28)), {0, 7, 14, 21}, {0, 14}, {0}]
    out = []
    for t, days in zip(its, on):
        name, rest = t.split(' - ', 1)
        cal = '<span class="ix-cal" aria-hidden="true">' + ''.join(
            f'<i{" class=on" if d in days else ""}></i>' for d in range(28)) + '</span>'
        out.append(f'{cal}<span class="ix-txt"><strong class="ix-meet-name">{name}</strong> - {rest}</span>')
    return build('ix-meet', out)


def absence(its):
    icons = ['phone', 'laptop-check', 'alert', 'user-x']
    out = []
    for n, (t, ic) in enumerate(zip(its, icons)):
        arrow = ('<span class="ix-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false">'
                 '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg></span>') if n == 0 else ''
        out.append(f'{ico(ic)}<span class="ix-txt">{t}</span>{arrow}')
    return build('ix-absence', out)


def claim(its):
    icons = ['mail', 'wallet', 'receipt', 'send', 'check-circle', 'swap']
    out = [f'<span class="ix-node">{ico(ic)}</span><span class="ix-txt">{t}</span>' for t, ic in zip(its, icons)]
    return build('ix-steps', out)


TRANSFORMS = [
    ('<li><strong>ILT</strong>', simple('ix-modes', ['present', 'laptop-play', 'wrench', 'refresh'])),
    ('<li>daily morning meeting - conducted', meetings),
    ('<li>Physical contact or advances', simple('ix-ban', ['hand', 'msg-alert', 'msg-dots', 'monitor', 'phone-img'], badge='ban')),
    ('<li>Display the names and contact details of the IC', simple('ix-duty', ['board', 'user-plus', 'cal-check', 'cap', 'file-up', 'mail'], badge='tick')),
    ('<li>Reason for leaving', simple('ix-topics', ['logout', 'users', 'building', 'trend', 'rupee', 'thumb', 'msg-text'])),
    ('<li>Salary dues must be settled within', simple('ix-settle', ['cash', 'award', 'bank', 'trophy', 'scale', 'file-check'])),
    ('<li>Inform the reporting manager before the day starts', absence),
    ('<li>Get written approval before travelling', claim),
    ('<li>Travel by the cheapest sensible option', simple('ix-rules', ['tag-down', 'users', 'receipt', 'suitcase', 'car', 'clock'])),
    ('<li>New employees receive 2 sets', simple('ix-uniform', ['user-plus', 'cal-check', 'bag', 'drop', 'refresh'], badge='shirt')),
]

IX_CSS = r'''
<style id="jx-ix-css">
/* Contextual list infographics. Every word is the manual's own; icons are decorative (aria-hidden). */
#jxView ul.ix{list-style:none;margin:20px 0 26px;padding:0;max-width:100%;display:grid;gap:12px;flex-direction:initial}
#jxView ul.ix > li{position:relative;margin:0;padding:0;max-width:none;color:var(--grey-700);font-size:14.5px;line-height:1.55}
#jxView ul.ix > li::before,#jxView ul.ix > li::after{content:none !important;display:none !important}
#jxView ul.ix .ix-txt{display:block;min-width:0}
#jxView ul.ix .ix-ico{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:12px;background:var(--ink);color:#fff;flex:0 0 auto}
#jxView ul.ix .ix-ico svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}
#jxView ul.ix .ix-badge{position:absolute;display:inline-flex;align-items:center;justify-content:center;border-radius:50%}
#jxView ul.ix .ix-badge svg{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round}

/* shared card */
#jxView ul.ix-modes > li,#jxView ul.ix-ban > li,#jxView ul.ix-duty > li,#jxView ul.ix-topics > li,#jxView ul.ix-rules > li,#jxView ul.ix-uniform > li,#jxView ul.ix-meet > li{
  background:#fff;border:1px solid var(--line-200);border-radius:16px;padding:18px}
#jxView ul.ix-modes .ix-txt,#jxView ul.ix-ban .ix-txt,#jxView ul.ix-duty .ix-txt,#jxView ul.ix-topics .ix-txt,#jxView ul.ix-rules .ix-txt,#jxView ul.ix-uniform .ix-txt{margin-top:14px}

/* 1 training modes (ILT / LMS / OJT / Refresher) */
#jxView ul.ix-modes{grid-template-columns:repeat(4,minmax(0,1fr))}
#jxView ul.ix-modes .ix-ico{width:52px;height:52px;border-radius:50%}
#jxView ul.ix-modes .ix-ico svg{width:26px;height:26px}
#jxView ul.ix-modes strong{display:block;font-size:20px;line-height:1.15;color:var(--ink);margin-bottom:4px}

/* 2 meetings: a 4-week calendar marks the days each meeting is held */
#jxView ul.ix-meet{grid-template-columns:repeat(4,minmax(0,1fr))}
#jxView ul.ix-meet .ix-cal{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:14px;padding:10px;border-radius:10px;background:#F3F3F2}
#jxView ul.ix-meet .ix-cal i{display:block;aspect-ratio:1;border-radius:3px;background:#fff;border:1px solid var(--line-200)}
#jxView ul.ix-meet .ix-cal i.on{background:var(--ink);border-color:var(--ink)}
#jxView ul.ix-meet .ix-meet-name{display:block;font-size:16px;color:var(--ink);margin-bottom:2px}

/* 3 POSH - what counts: each act carries a "not allowed" sign */
#jxView ul.ix-ban{grid-template-columns:repeat(3,minmax(0,1fr))}
#jxView ul.ix-ban > li:last-child{grid-column:span 2}
#jxView ul.ix-ban .ix-ico{background:#F1F1F0;color:var(--ink)}
#jxView ul.ix-ban .ix-badge{left:44px;top:44px;width:24px;height:24px;background:#fff;color:#B42318}
#jxView ul.ix-ban .ix-badge svg{width:24px;height:24px;stroke-width:2.6}

/* 4 POSH - dealership duties: checklist */
#jxView ul.ix-duty{grid-template-columns:repeat(3,minmax(0,1fr))}
#jxView ul.ix-duty .ix-badge{right:16px;top:16px;width:24px;height:24px;border:1.5px solid var(--ink);color:var(--ink)}
#jxView ul.ix-duty .ix-badge svg{width:14px;height:14px;stroke-width:3}

/* 5 exit interview topics */
#jxView ul.ix-topics{grid-template-columns:repeat(4,minmax(0,1fr))}
#jxView ul.ix-topics > li{display:flex;flex-direction:column}
#jxView ul.ix-topics .ix-ico{background:#F1F1F0;color:var(--ink)}
#jxView ul.ix-topics .ix-txt{color:var(--ink);font-weight:500}

/* 6 full & final settlement statement */
#jxView ul.ix-settle{grid-template-columns:repeat(2,minmax(0,1fr));gap:0;background:#fff;border:1px solid var(--line-200);border-radius:16px;overflow:hidden}
#jxView ul.ix-settle > li{display:grid;grid-template-columns:44px minmax(0,1fr);gap:14px;align-items:center;padding:16px 18px;border-bottom:1px solid var(--line-100)}
#jxView ul.ix-settle > li:nth-child(odd){border-right:1px solid var(--line-100)}
#jxView ul.ix-settle > li:nth-last-child(-n+2){border-bottom:0}

/* 7 cannot come to work: do this -> then this; otherwise the consequences */
#jxView ul.ix-absence{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 44px}
#jxView ul.ix-absence > li{display:grid;grid-template-columns:44px minmax(0,1fr);gap:14px;align-items:start;padding:18px;border-radius:16px;background:#fff;border:1px solid var(--line-200)}
#jxView ul.ix-absence > li:nth-child(n+3){background:#FFF8F6;border-color:#F2C7BE;border-top:4px solid #B42318}
#jxView ul.ix-absence > li:nth-child(n+3) .ix-ico{background:#B42318}
#jxView ul.ix-absence > li:nth-child(4){background:#FCEDEA}
#jxView ul.ix-absence .ix-arrow{position:absolute;right:-36px;top:50%;width:28px;height:28px;margin-top:-14px;color:var(--ink);display:flex}
#jxView ul.ix-absence .ix-arrow svg{width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}

/* 8 how to claim: numbered timeline */
#jxView ul.ix-steps{grid-template-columns:repeat(6,minmax(0,1fr));gap:0;counter-reset:ixs;padding-top:10px}
#jxView ul.ix-steps > li{counter-increment:ixs;padding:0 10px;font-size:13.5px}
#jxView ul.ix-steps .ix-node{position:relative;display:flex;align-items:center;margin-bottom:14px}
#jxView ul.ix-steps .ix-node::before{content:"";position:absolute;left:44px;right:-20px;top:50%;border-top:2px dashed var(--grey-300)}
#jxView ul.ix-steps > li:last-child .ix-node::before{display:none}
#jxView ul.ix-steps .ix-ico{position:relative;border-radius:50%}
#jxView ul.ix-steps .ix-node::after{content:counter(ixs);position:absolute;left:30px;top:-6px;width:20px;height:20px;border-radius:50%;background:#fff;border:1.5px solid var(--ink);
  color:var(--ink);font-size:11px;font-weight:800;line-height:17px;text-align:center}

/* 9 travel rules */
#jxView ul.ix-rules{grid-template-columns:repeat(3,minmax(0,1fr))}
#jxView ul.ix-rules .ix-ico{background:#F1F1F0;color:var(--ink)}

/* 10 uniform policy: shirt badge on each */
#jxView ul.ix-uniform{grid-template-columns:repeat(5,minmax(0,1fr))}
#jxView ul.ix-uniform .ix-badge{left:46px;top:12px;width:26px;height:26px;background:#fff;border:1.5px solid var(--ink);color:var(--ink)}
#jxView ul.ix-uniform .ix-badge svg{width:15px;height:15px;stroke-width:2}

/* ---------- tablet */
@media (max-width:1100px){
  #jxView ul.ix-modes,#jxView ul.ix-meet,#jxView ul.ix-topics{grid-template-columns:repeat(2,minmax(0,1fr))}
  #jxView ul.ix-uniform,#jxView ul.ix-rules,#jxView ul.ix-duty{grid-template-columns:repeat(2,minmax(0,1fr))}
  #jxView ul.ix-ban{grid-template-columns:repeat(2,minmax(0,1fr))}
  #jxView ul.ix-ban > li:last-child{grid-column:1/-1}
  #jxView ul.ix-uniform > li:last-child{grid-column:1/-1}
  #jxView ul.ix-steps{grid-template-columns:1fr;gap:0}
  #jxView ul.ix-steps > li{position:relative;display:grid;grid-template-columns:44px minmax(0,1fr);gap:16px;padding:0 0 18px 0}
  #jxView ul.ix-steps .ix-node{position:static;margin:0;align-self:start}
  #jxView ul.ix-steps > li .ix-node::before{left:21px;right:auto;top:48px;height:calc(100% - 44px);border-top:0;border-left:2px dashed var(--grey-300)}
  #jxView ul.ix-steps .ix-node::after{left:30px;top:-6px}
  #jxView ul.ix-steps .ix-txt{padding-top:10px}
}
/* ---------- phone: one column, icon beside text */
@media (max-width:640px){
  #jxView ul.ix-modes,#jxView ul.ix-meet,#jxView ul.ix-topics,#jxView ul.ix-uniform,#jxView ul.ix-rules,#jxView ul.ix-duty,
  #jxView ul.ix-ban,#jxView ul.ix-settle,#jxView ul.ix-absence{grid-template-columns:1fr}
  #jxView ul.ix-ban > li:last-child,#jxView ul.ix-uniform > li:last-child{grid-column:auto}
  #jxView ul.ix-modes > li,#jxView ul.ix-ban > li,#jxView ul.ix-duty > li,#jxView ul.ix-topics > li,#jxView ul.ix-rules > li,#jxView ul.ix-uniform > li{
    display:grid;grid-template-columns:44px minmax(0,1fr);gap:14px;align-items:center;padding:14px}
  #jxView ul.ix-modes .ix-txt,#jxView ul.ix-ban .ix-txt,#jxView ul.ix-duty .ix-txt,#jxView ul.ix-topics .ix-txt,#jxView ul.ix-rules .ix-txt,#jxView ul.ix-uniform .ix-txt{margin-top:0}
  #jxView ul.ix-modes .ix-ico{width:44px;height:44px}
  #jxView ul.ix-modes .ix-ico svg{width:22px;height:22px}
  #jxView ul.ix-modes strong{font-size:17px}
  #jxView ul.ix-duty > li{padding-right:46px}
  #jxView ul.ix-duty .ix-badge{top:50%;margin-top:-12px;right:14px}
  #jxView ul.ix-ban .ix-badge{left:40px;top:40px;width:22px;height:22px}
  #jxView ul.ix-ban .ix-badge svg{width:22px;height:22px}
  #jxView ul.ix-uniform > li{padding-top:18px}
  #jxView ul.ix-uniform .ix-badge{left:42px;top:8px;width:22px;height:22px}
  #jxView ul.ix-uniform .ix-badge svg{width:13px;height:13px}
  #jxView ul.ix-meet > li{display:grid;grid-template-columns:112px minmax(0,1fr);gap:14px;align-items:center;padding:14px}
  #jxView ul.ix-meet .ix-cal{margin:0;padding:7px;gap:3px}
  #jxView ul.ix-meet .ix-cal i{border-radius:2px}
  #jxView ul.ix-settle > li{border-right:0 !important;border-bottom:1px solid var(--line-100) !important}
  #jxView ul.ix-settle > li:last-child{border-bottom:0 !important}
  #jxView ul.ix-absence{gap:28px}
  #jxView ul.ix-absence .ix-arrow{right:auto;left:50%;top:auto;bottom:-28px;margin:0 0 0 -12px;width:24px;height:24px;transform:rotate(90deg)}
  #jxView ul.ix-absence .ix-arrow svg{width:24px;height:24px}
  #jxView ul.ix-absence > li:nth-child(2){margin-bottom:8px}
  #jxView ul.ix > li{font-size:14px}
}
</style>
'''


# ------------------------------------------------------------------ helpers
def chapter_text(s):
    a = s.find('<article class="jx-chapter"')
    b = s.find('</main>', a)
    t = re.sub(r'<style.*?</style>|<script.*?</script>|<!--.*?-->|<svg.*?</svg>', '', s[a:b], flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def strip_previous(s):
    s = re.sub(r'<!--jsw-logo-sprite-->.*?<!--/jsw-logo-sprite-->', '', s, flags=re.S)
    s = re.sub(r'<!--jsw-favicon-->.*?<!--/jsw-favicon-->', '', s, flags=re.S)
    s = re.sub(r'\n?<style id="jx-logo-css">.*?</style>\n?', '', s, flags=re.S)
    s = re.sub(r'\n?<style id="jx-ix-css">.*?</style>\n?', '', s, flags=re.S)
    s = re.sub(r'<svg class="jx-logo[^"]*"[^>]*><use href="#jsw-mark-[hes]"/></svg>', '', s)
    s = re.sub(r'<div class="jx-hero-brand">\s*</div>', '', s)
    s = re.sub(r'<!--ix-orig:([A-Za-z0-9+/=]+)-->.*?<!--/ix-->',
               lambda m: base64.b64decode(m.group(1)).decode('utf-8'), s, flags=re.S)
    s = re.sub(r'<ul class="list-clean ix ix-[a-z]+">', '<ul class="list-clean">', s)  # first-generation
    return s


def apply(s):
    s = strip_previous(s)
    before = chapter_text(s)

    s = s.replace('</title>', '</title>' + FAVICON, 1)
    i = s.find('</head>')
    s = s[:i] + LOGO_CSS + IX_CSS + s[i:]
    m = re.search(r'<body[^>]*>', s)
    s = s[:m.end()] + SPRITE + s[m.end():]

    def sub(pat, rep, count=1):
        nonlocal s
        s2, n = re.subn(pat, rep, s, count=count, flags=re.S)
        assert n >= 1, pat
        s = s2
        return n

    sub(r'(<button class="jx-top-brand"[^>]*>)\s*(</button>)', r'\1' + H() + E() + r'\2')
    sub(r'(<button class="jx-nav-brand"[^>]*>)(\s*<span>HROS</span>)', r'\1' + H() + r'\2')
    sub(r'(<div class="jx-hero-glow" aria-hidden="true"></div>)', r'\1<div class="jx-hero-brand">' + H() + '</div>')
    sub(r'(<footer class="jx-foot">)', r'\1' + H())
    n = sub(r'(<header class="jx-head"><div class="jx-head-row"><div>.*?</div>)(</div></header>)',
            r'\1' + E('jx-head-mark', label=False) + r'\2', count=0)
    assert n == 15, n
    n = sub(r'(<div class="annex-modal-header">)', r'\1' + H('jx-modal-mark'), count=0)
    assert n == 2, n

    for anchor, fn in TRANSFORMS:
        assert s.count(anchor) == 1, anchor
        i = s.find(anchor)
        j = s.rfind('<ul class="list-clean">', 0, i)
        assert j != -1 and s[j:i].count('<li') == 0, anchor
        k = s.find('</ul>', i) + 5
        orig = s[j:k]
        new = fn(items(orig))
        s = s[:j] + '<!--ix-orig:' + base64.b64encode(orig.encode('utf-8')).decode() + '-->' + new + '<!--/ix-->' + s[k:]

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
