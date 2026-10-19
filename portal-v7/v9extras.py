"""V9 (13.10.26) additions: native, interactive versions of V9's new pictures and
reviewer-flagged lists. Every visible word comes from the V9 docx — its
paragraphs, or the text printed inside its own images (transcribed below)."""
import html
import re

esc = lambda s: html.escape(s, quote=False)

IMG_ONEAPP = '8746a180'      # About the Manual — JSW-OneApp ecosystem picture
IMG_ATTRITION = '64fb8e5d'   # 11.2 Impact of attrition — "sample diagram given below"

# ── text printed in the JSW-OneApp picture ──
ONEAPP = {
    'title': 'One Platform. One Ecosystem. One Digital Experience.',
    'sub': 'A unified enterprise platform connecting People, Learning, Compliance and Dealership Audits',
    'hub': 'JSW-OneApp',
    # (key, title, bullets, verb in the picture's footer strip)
    'mods': [
        ('rms', 'RMS — Recruitment Management System',
         ['End-to-end recruitment lifecycle', 'Candidate tracking and hiring workflows',
          'Structured recruitment processes', 'Centralized candidate information'], 'Recruit'),
        ('lms', 'LMS — Learning Management System',
         ['Digital learning & knowledge repository', 'Role-based learning journeys',
          'Course/content management', 'Learning progress and completion tracking'], 'Learn'),
        ('tms', 'TMS — Training Management System',
         ['Training planning and scheduling', 'Dealer & employee training management',
          'Trainer / participant management', 'Training effectiveness and certification tracking'], 'Train'),
        ('audit', 'Dealer Audit',
         ['Standardized audit checklists', 'Digital audit execution',
          'Findings, observations and corrective actions', 'Compliance tracking and dashboards'], 'Audit'),
        ('sop', 'HR / SOP',
         ['Centralized HR policies & SOPs', 'Easy access to organizational knowledge',
          'Searchable policy and process repository'], 'Standardize'),
    ],
}

ICONS = {  # simple line icons echoing the picture's glyphs
    'rms': '<circle cx="9" cy="9" r="3.2"/><circle cx="15.5" cy="10.5" r="3.2"/><path d="M3 20c.8-3 3.2-4.6 6-4.6M11 21c.8-3 3-4.4 5.5-4.4S21 18 21.5 21"/>',
    'lms': '<path d="M4 4h7v16H4zM13 4h7v16h-7z"/>',
    'tms': '<rect x="3" y="4" width="16" height="11" rx="1.2"/><path d="M19 5l2.5-1.5v4L19 6"/><circle cx="7" cy="18.5" r="2"/>',
    'audit': '<path d="M12 3l8 5.5-3 11H7l-3-11z"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
    'sop': '<rect x="5" y="3" width="14" height="18" rx="1.2"/><path d="M8.5 8h7M8.5 12h7M8.5 16h5"/>',
}


def _icon(k):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[k]}</svg>')


def oneapp():
    o = ONEAPP
    nodes, verbs = [], []
    for i, (k, title, bullets, verb) in enumerate(o['mods']):
        li = ''.join(f'<li>{esc(b)}</li>' for b in bullets)
        nodes.append(
            f'<div class="v9-hub-node" data-k="{k}" style="--slot:{i}">'
            f'<button type="button" class="v9-hub-btn" aria-pressed="false">'
            f'<span class="v9-hub-ic">{_icon(k)}</span><span class="v9-hub-t">{esc(title)}</span></button>'
            f'<ul class="v9-hub-list" id="v9hub-{k}">{li}</ul></div>')
        verbs.append(f'<button type="button" class="v9-hub-verb" data-k="{k}">'
                     f'<span class="v9-hub-ic">{_icon(k)}</span>{esc(verb)}</button>')
    return (f'<figure class="v9-hub" data-v9="hub">'
            f'<figcaption class="v9-hub-head"><span class="v9-hub-title">{esc(o["title"])}</span>'
            f'<span class="v9-hub-sub">{esc(o["sub"])}</span></figcaption>'
            f'<div class="v9-hub-stage">'
            f'<svg class="v9-hub-wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"></svg>'
            f'<div class="v9-hub-core"><span class="v9-hub-ring"></span><b>{esc(o["hub"])}</b></div>'
            f'{"".join(nodes)}</div>'
            f'<div class="v9-hub-verbs" role="group">{"".join(verbs)}</div></figure>')


# ── text and values printed in the attrition sample diagram ──
ATTR = {
    'y': 'Productivity', 'x': 'Impact Month',
    'pts': [('M-3', 2.6, ''), ('M-2', 2.1, ''), ('M-1', 1.0, ''), ('M', None, 'RM Left'),
            ('M+1', 1.1, 'New Hire'), ('M+2', 1.5, ''), ('M+3', 1.5, ''), ('M+4', 1.5, '')],
    'bands': [(0, 3, 'Performance drop before leaving', 'Performance loss due to demotivation & manpower exit'),
              (4, 7, 'Low Productivity due to new manpower', 'New joiner catching up')],
}


def attrition():
    a = ATTR
    W, H, L, R, T, B = 760, 330, 56, 24, 22, 52
    n = len(a['pts'])
    xs = [L + i * (W - L - R) / (n - 1) for i in range(n)]
    ymax = 3.0
    yv = lambda v: T + (H - T - B) * (1 - v / ymax)
    # the picture's lowest point (RM Left) carries no value label; draw it at the trough
    vals = [v if v is not None else 0.25 for _, v, _ in a['pts']]
    ys = [yv(v) for v in vals]
    # smooth path (Catmull-Rom → cubic Bézier)
    d = f'M{xs[0]:.1f},{ys[0]:.1f}'
    for i in range(n - 1):
        x0, y0 = (xs[i - 1], ys[i - 1]) if i else (xs[i], ys[i])
        x1, y1, x2, y2 = xs[i], ys[i], xs[i + 1], ys[i + 1]
        x3, y3 = (xs[i + 2], ys[i + 2]) if i + 2 < n else (x2, y2)
        c1 = (x1 + (x2 - x0) / 6, y1 + (y2 - y0) / 6)
        c2 = (x2 - (x3 - x1) / 6, y2 - (y3 - y1) / 6)
        d += f' C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {x2:.1f},{y2:.1f}'
    base = H - B
    area = d + f' L{xs[-1]:.1f},{base} L{xs[0]:.1f},{base} Z'
    bands = []
    for j, (s, e, label, note) in enumerate(a['bands']):
        x0, x1 = xs[s], xs[e]
        bands.append(f'<rect class="v9-at-band" data-b="{j}" x="{x0:.1f}" y="{T}" width="{x1 - x0:.1f}" height="{base - T}"/>')
    grid = ''.join(f'<line class="v9-at-grid" x1="{x:.1f}" x2="{x:.1f}" y1="{T}" y2="{base}"/>' for x in xs)
    ticks = ''.join(f'<text class="v9-at-tick" x="{x:.1f}" y="{base + 20}">{esc(m)}</text>' for x, (m, _, _) in zip(xs, a['pts']))
    pts = []
    for i, ((m, v, tag), x, y) in enumerate(zip(a['pts'], xs, ys)):
        lab = f'{v:.1f}' if v is not None else ''
        aria = ', '.join(p for p in (m, lab, tag) if p)
        val = f'<g class="v9-at-val"><rect x="{x - 20:.1f}" y="{y - 34:.1f}" width="40" height="22" rx="4"/><text x="{x:.1f}" y="{y - 18.5:.1f}">{lab}</text></g>' if lab else ''
        ty = y + 26 if lab else y - 16      # the unlabelled trough carries its tag above the point
        tg = f'<text class="v9-at-tag" x="{x:.1f}" y="{ty:.1f}">{esc(tag)}</text>' if tag else ''
        band = 0 if i <= 3 else 1
        pts.append(f'<g class="v9-at-pt" tabindex="0" role="img" aria-label="{esc(aria)}" data-b="{band}">'
                   f'<circle class="v9-at-hit" cx="{x:.1f}" cy="{y:.1f}" r="18"/>'
                   f'<circle class="v9-at-dot" cx="{x:.1f}" cy="{y:.1f}" r="6"/>{val}{tg}</g>')
    svg = (f'<svg class="v9-at-svg" viewBox="0 0 {W} {H}" role="group" aria-label="{esc(a["y"])} / {esc(a["x"])}">'
           f'{"".join(bands)}{grid}'
           f'<path class="v9-at-area" d="{area}"/><path class="v9-at-line" d="{d}"/>'
           f'<line class="v9-at-axis" x1="{L}" x2="{L}" y1="{T - 8}" y2="{base}"/>'
           f'<line class="v9-at-axis" x1="{L}" x2="{W - R + 6}" y1="{base}" y2="{base}"/>'
           f'<text class="v9-at-ylab" transform="translate(18 {(T + base) / 2:.0f}) rotate(-90)">{esc(a["y"])}</text>'
           f'{ticks}<text class="v9-at-xlab" x="{L}" y="{H - 6}">{esc(a["x"])}</text>'
           f'{"".join(pts)}</svg>')
    keys = ''.join(f'<button type="button" class="v9-at-key" data-b="{j}" aria-pressed="false">'
                   f'<b>{esc(label)}</b><span>{esc(note)}</span></button>'
                   for j, (_, _, label, note) in enumerate(a['bands']))
    return f'<figure class="v9-attr" data-v9="attr"><div class="v9-at-scroll">{svg}</div><div class="v9-at-keys">{keys}</div></figure>'


# ── 6. Learning design techniques (reviewer comment: "Infographic") ──
def learning_design(items):
    """items: docx list lines 'Name: description'. Shown as a selectable strip + detail."""
    rows = []
    for t in items:
        name, _, desc = t.partition(': ')
        rows.append((name.strip(), desc.strip()))
    tabs, panels = [], []
    for i, (name, desc) in enumerate(rows):
        sel = 'true' if i == 0 else 'false'
        tabs.append(f'<button type="button" role="tab" class="v9-ld-tab" id="v9ld-t{i}" aria-selected="{sel}" '
                    f'aria-controls="v9ld-p{i}" tabindex="{0 if i == 0 else -1}"><span class="v9-ld-n">{i + 1}</span>{esc(name)}</button>')
        vis = _ld_visual(name, desc)
        panels.append(f'<div role="tabpanel" class="v9-ld-panel" id="v9ld-p{i}" aria-labelledby="v9ld-t{i}"{"" if i == 0 else " hidden"}>'
                      f'<p class="v9-ld-name"><strong>{esc(name)}</strong>: {esc(desc)}</p>{vis}</div>')
    return (f'<figure class="v9-ld" data-v9="ld"><div class="v9-ld-tabs" role="tablist">{"".join(tabs)}</div>'
            f'{"".join(panels)}</figure>')


def _ld_visual(name, desc):
    """Visual built only from the words already in the item."""
    n = name.lower()
    if n.startswith('addie'):
        steps = [s.strip() for s in desc.split(',')]
        return ('<ol class="v9-ld-cycle">' + ''.join(
            f'<li><b>{esc(s[0])}</b><span>{esc(s)}</span></li>' for s in steps) + '</ol>')
    if n.startswith('70:20:10'):
        m = re.match(r'Learn from (.+?), (.+?) and (.+)$', desc)
        if m:
            parts = list(zip(('70', '20', '10'), m.groups()))
            return ('<div class="v9-ld-bar">' + ''.join(
                f'<div style="flex:{p}"><b>{p}</b><span>{esc(w)}</span></div>' for p, w in parts) + '</div>')
    return ''


# ── Annexure: List of Compliances ──
def compliances(blocks):
    items = [b['text'] for b in blocks if b['k'] == 'p' and b['text']]
    head, acts = items[0], items[1:]
    assert head == 'Governing Act', head
    cards = ''.join(f'<li class="v9-cp-item"><span class="v9-cp-n">{i}</span><span class="v9-cp-t">{esc(a)}</span></li>'
                    for i, a in enumerate(acts, 1))
    return (f'<div class="v9-cp" data-v9="cp"><h3 class="sub-title subhead">{esc(head)}</h3>'
            f'<ol class="v9-cp-list">{cards}</ol></div>')


CSS = r'''
/* ── V9 infographics (monochrome, matches flow.css) ── */
.jx-chapter .v9-hub{margin:26px 0 34px;padding:0}
.v9-hub-head{display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center;margin-bottom:22px}
.v9-hub-title{font-family:var(--font-display,'Manrope',sans-serif);font-weight:800;font-size:clamp(19px,2.4vw,26px);letter-spacing:-.02em;color:var(--ink,#151515);line-height:1.15}
.v9-hub-sub{font-size:14px;color:#55565b;max-width:56ch}
.v9-hub-stage{position:relative;display:grid;grid-template-columns:1fr minmax(150px,190px) 1fr;grid-template-rows:auto auto auto;gap:18px 28px;align-items:center}
.v9-hub-wires{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible}
.v9-hub-wires line{stroke:#9a9a9f;stroke-width:1.4;vector-effect:non-scaling-stroke;stroke-dasharray:3 4;transition:stroke .2s}
.v9-hub-wires line.on{stroke:var(--ink,#151515);stroke-dasharray:none;stroke-width:2}
.v9-hub-core{grid-column:2;grid-row:2;position:relative;aspect-ratio:1;border-radius:50%;display:grid;place-items:center;background:#fff;border:2px solid var(--ink,#151515);z-index:1;text-align:center;padding:10px}
.v9-hub-core b{font-family:var(--font-display,'Manrope',sans-serif);font-size:17px;font-weight:800;letter-spacing:-.01em;color:var(--ink,#151515)}
.v9-hub-ring{position:absolute;inset:-12px;border-radius:50%;border:1px solid #c9c9cc}
.v9-hub-node{position:relative;z-index:1;background:#fff;border:1px solid var(--line-200,#dcdcdc);border-radius:10px;transition:border-color .2s,box-shadow .2s}
.v9-hub-node[data-k=rms]{grid-column:1/-1;grid-row:1;justify-self:center;width:min(100%,430px)}
.v9-hub-node[data-k=sop]{grid-column:1;grid-row:2}
.v9-hub-node[data-k=lms]{grid-column:3;grid-row:2}
.v9-hub-node[data-k=audit]{grid-column:1;grid-row:3}
.v9-hub-node[data-k=tms]{grid-column:3;grid-row:3}
.v9-hub-btn{all:unset;box-sizing:border-box;display:flex;align-items:center;gap:10px;width:100%;padding:12px 14px 6px;cursor:pointer;font-weight:700;font-size:14.5px;color:var(--ink,#151515);line-height:1.3}
.v9-hub-btn:focus-visible,.v9-hub-verb:focus-visible,.v9-at-key:focus-visible,.v9-ld-tab:focus-visible{outline:2px solid var(--ink,#151515);outline-offset:2px}
.v9-hub-ic{flex:none;display:grid;place-items:center;width:32px;height:32px;border-radius:7px;background:#efefef;color:var(--ink,#151515)}
.v9-hub-ic svg{width:19px;height:19px}
.v9-hub-list{list-style:disc;margin:0;padding:2px 14px 12px 58px;font-size:13.5px;color:#3a3b40;line-height:1.5}
.v9-hub.has-active .v9-hub-node:not(.is-on) .v9-hub-btn,.v9-hub.has-active .v9-hub-node:not(.is-on) .v9-hub-list{color:#a3a3a8}
.v9-hub.has-active .v9-hub-node:not(.is-on) .v9-hub-ic{opacity:.45}
.v9-hub-node.is-on{border-color:var(--ink,#151515);box-shadow:0 10px 24px -16px rgba(17,17,19,.55)}
.v9-hub-node.is-on .v9-hub-ic,.v9-hub-verb.is-on .v9-hub-ic{background:var(--ink,#151515);color:#fff}
.v9-hub-verbs{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:22px;padding:10px;border:1px solid var(--line-200,#dcdcdc);border-radius:10px;background:#fff}
.v9-hub-verb{all:unset;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:8px;padding:8px 6px;border-radius:7px;cursor:pointer;font-weight:700;font-size:14px;color:var(--ink,#151515)}
.v9-hub-verb:hover,.v9-hub-verb.is-on{background:#f1f1f1}
@media(max-width:760px){
  .v9-hub-stage{grid-template-columns:1fr;grid-template-rows:none}
  .v9-hub-wires{display:none}
  .v9-hub-core{grid-column:1;grid-row:1;width:150px;justify-self:center;margin-bottom:6px}
  .v9-hub-node[data-k]{grid-column:1;grid-row:auto;margin:0;width:auto;justify-self:stretch}
  .v9-hub-verbs{grid-template-columns:repeat(auto-fit,minmax(110px,1fr))}
}

.jx-chapter .v9-attr{margin:22px 0 30px}
.v9-at-scroll{overflow-x:auto;border:1px solid var(--line-200,#dcdcdc);border-radius:10px;background:#fff;padding:8px 6px 0}
.v9-at-svg{display:block;width:100%;min-width:560px;height:auto;font-family:inherit}
.v9-at-band{fill:transparent;transition:fill .2s}
.v9-attr[data-on="0"] .v9-at-band[data-b="0"],.v9-attr[data-on="1"] .v9-at-band[data-b="1"]{fill:rgba(27,27,29,.07)}
.v9-at-grid{stroke:#d5d5d8;stroke-dasharray:3 4}
.v9-at-axis{stroke:var(--ink,#151515);stroke-width:1.5}
.v9-at-area{fill:rgba(27,27,29,.12)}
.v9-at-line{fill:none;stroke:var(--ink,#151515);stroke-width:2.6;stroke-linecap:round}
.v9-at-tick{font-size:12px;font-weight:700;fill:#3a3b40;text-anchor:middle}
.v9-at-xlab,.v9-at-ylab{font-size:12px;font-weight:700;fill:#55565b}
.v9-at-ylab{text-anchor:middle}
.v9-at-pt{cursor:pointer;outline:none}
.v9-at-hit{fill:transparent}
.v9-at-dot{fill:#fff;stroke:var(--ink,#151515);stroke-width:2.4;transition:r .15s}
.v9-at-val rect{fill:#fff;stroke:var(--ink,#151515);stroke-width:1.2}
.v9-at-val text{font-size:12.5px;font-weight:800;text-anchor:middle;fill:var(--ink,#151515)}
.v9-at-tag{font-size:11.5px;font-weight:700;text-anchor:middle;fill:var(--ink,#151515)}
.v9-at-pt:hover .v9-at-dot,.v9-at-pt:focus .v9-at-dot{r:8;fill:var(--ink,#151515)}
.v9-at-pt:hover .v9-at-val rect,.v9-at-pt:focus .v9-at-val rect{fill:var(--ink,#151515)}
.v9-at-pt:hover .v9-at-val text,.v9-at-pt:focus .v9-at-val text{fill:#fff}
.v9-attr[data-on="0"] .v9-at-pt[data-b="1"],.v9-attr[data-on="1"] .v9-at-pt[data-b="0"]{opacity:.35}
.v9-at-keys{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
.v9-at-key{all:unset;box-sizing:border-box;display:flex;flex-direction:column;gap:3px;padding:10px 14px;border:1px solid var(--line-200,#dcdcdc);border-radius:9px;background:#fff;cursor:pointer;font-size:13.5px;color:#3a3b40}
.v9-at-key b{color:var(--ink,#151515);font-size:14px}
.v9-at-key[aria-pressed=true]{border-color:var(--ink,#151515);background:#f4f4f4}
@media(max-width:620px){.v9-at-keys{grid-template-columns:1fr}}

.jx-chapter .v9-ld{margin:14px 0 26px;border:1px solid var(--line-200,#dcdcdc);border-radius:10px;background:#fff;overflow:hidden}
.v9-ld-tabs{display:flex;flex-wrap:wrap;gap:0;border-bottom:1px solid var(--line-200,#dcdcdc);background:#f6f6f6}
.v9-ld-tab{all:unset;box-sizing:border-box;flex:1 1 150px;display:flex;align-items:center;gap:8px;padding:11px 14px;cursor:pointer;font-weight:700;font-size:13.5px;color:#55565b;border-bottom:2px solid transparent;line-height:1.25}
.v9-ld-tab[aria-selected=true]{color:var(--ink,#151515);border-bottom-color:var(--ink,#151515);background:#fff}
.v9-ld-n{flex:none;display:grid;place-items:center;width:22px;height:22px;border-radius:50%;border:1.5px solid currentColor;font-size:11.5px}
.v9-ld-tab[aria-selected=true] .v9-ld-n{background:var(--ink,#151515);border-color:var(--ink,#151515);color:#fff}
.v9-ld-panel{padding:18px 20px 22px}
.v9-ld-name{margin:0 0 14px}
.v9-ld-cycle{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,1fr);gap:10px;counter-reset:none}
.v9-ld-cycle li{position:relative;display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center;font-weight:700;font-size:13.5px;color:var(--ink,#151515)}
.v9-ld-cycle li b{display:grid;place-items:center;width:46px;height:46px;border-radius:50%;background:var(--ink,#151515);color:#fff;font-size:18px}
.v9-ld-cycle li:not(:last-child)::after{content:'';position:absolute;top:23px;left:calc(50% + 30px);right:calc(-50% + 30px);height:2px;background:#9a9a9f}
.v9-ld-bar{display:flex;gap:4px;border-radius:8px;overflow:hidden}
.v9-ld-bar div{display:flex;flex-direction:column;gap:2px;padding:12px 12px;background:#e9e9ea;min-width:0}
.v9-ld-bar div:first-child{background:var(--ink,#151515);color:#fff}
.v9-ld-bar div:nth-child(2){background:#6c6c70;color:#fff}
.v9-ld-bar b{font-size:20px;font-weight:800}
.v9-ld-bar span{font-size:13px;overflow-wrap:anywhere}
@media(max-width:620px){.v9-ld-cycle{grid-template-columns:1fr;gap:8px}.v9-ld-cycle li{flex-direction:row;text-align:left}.v9-ld-cycle li b{width:36px;height:36px;font-size:15px}.v9-ld-cycle li::after{display:none}.v9-ld-bar{flex-direction:column}.v9-ld-bar div{flex:none!important}}

.v9-cp-list{list-style:none;margin:6px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.v9-cp-item{display:flex;align-items:center;gap:12px;padding:14px 16px;border:1px solid var(--line-200,#dcdcdc);border-radius:10px;background:#fff;font-weight:600;color:var(--ink,#151515);line-height:1.35}
.v9-cp-n{flex:none;display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--ink,#151515);color:#fff;font-size:13px;font-weight:800}
@media (prefers-reduced-motion:reduce){.v9-hub-node,.v9-at-band,.v9-at-dot,.v9-hub-wires line{transition:none}}
'''

JS = r'''
<script id="jx-v9-js">
(function(){
  /* JSW-OneApp hub: wires + select a module from its card or the footer strip */
  function wire(fig){
    var stage = fig.querySelector('.v9-hub-stage'), svg = fig.querySelector('.v9-hub-wires'), core = fig.querySelector('.v9-hub-core');
    if(!stage || !svg || !core) return;
    var r = stage.getBoundingClientRect(); if(!r.width) return;
    var c = core.getBoundingClientRect(), cx = c.left + c.width/2 - r.left, cy = c.top + c.height/2 - r.top;
    var out = '';
    fig.querySelectorAll('.v9-hub-node').forEach(function(n){
      var b = n.getBoundingClientRect(), nx = b.left + b.width/2 - r.left, ny = b.top + b.height/2 - r.top;
      if(n.dataset.k === 'rms') ny = b.bottom - r.top;
      out += '<line data-k="' + n.dataset.k + '" x1="' + (cx/r.width*100) + '" y1="' + (cy/r.height*100) + '" x2="' + (nx/r.width*100) + '" y2="' + (ny/r.height*100) + '"' + (n.classList.contains('is-on') ? ' class="on"' : '') + '/>';
    });
    svg.innerHTML = out;
  }
  function pick(fig, k){
    var cur = fig.dataset.on === k ? '' : k;
    fig.dataset.on = cur;
    fig.classList.toggle('has-active', !!cur);
    fig.querySelectorAll('.v9-hub-node').forEach(function(n){
      var on = n.dataset.k === cur; n.classList.toggle('is-on', on);
      n.querySelector('.v9-hub-btn').setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    fig.querySelectorAll('.v9-hub-verb').forEach(function(v){ v.classList.toggle('is-on', v.dataset.k === cur); v.setAttribute('aria-pressed', v.dataset.k === cur ? 'true' : 'false'); });
    fig.querySelectorAll('.v9-hub-wires line').forEach(function(l){ l.classList.toggle('on', l.dataset.k === cur); });
  }
  document.addEventListener('click', function(e){
    var t = e.target.closest && e.target.closest('.v9-hub-btn, .v9-hub-verb');
    if(t){ var fig = t.closest('.v9-hub'); pick(fig, t.closest('[data-k]').dataset.k); return; }
    var k = e.target.closest && e.target.closest('.v9-at-key');
    if(k){ var f = k.closest('.v9-attr'), b = k.dataset.b, on = f.dataset.on === b ? '' : b;
      f.dataset.on = on; f.querySelectorAll('.v9-at-key').forEach(function(x){ x.setAttribute('aria-pressed', x.dataset.b === on ? 'true' : 'false'); }); return; }
    var tab = e.target.closest && e.target.closest('.v9-ld-tab');
    if(tab) ldSelect(tab);
  });
  /* attrition chart: hovering a point lights its phase */
  ['mouseover','focusin'].forEach(function(ev){ document.addEventListener(ev, function(e){
    var p = e.target.closest && e.target.closest('.v9-at-pt'); if(!p) return;
    var f = p.closest('.v9-attr'); if(!f.querySelector('.v9-at-key[aria-pressed=true]')) f.dataset.on = p.dataset.b;
  }); });
  ['mouseout','focusout'].forEach(function(ev){ document.addEventListener(ev, function(e){
    var p = e.target.closest && e.target.closest('.v9-at-pt'); if(!p) return;
    var f = p.closest('.v9-attr'); if(!f.querySelector('.v9-at-key[aria-pressed=true]')) f.dataset.on = '';
  }); });
  /* learning design tabs (roving tabindex + arrow keys) */
  function ldSelect(tab){
    var fig = tab.closest('.v9-ld');
    fig.querySelectorAll('.v9-ld-tab').forEach(function(t){
      var on = t === tab; t.setAttribute('aria-selected', on ? 'true' : 'false'); t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    });
  }
  document.addEventListener('keydown', function(e){
    var tab = e.target.closest && e.target.closest('.v9-ld-tab'); if(!tab) return;
    var all = [].slice.call(tab.parentNode.children), i = all.indexOf(tab), j = -1;
    if(e.key === 'ArrowRight') j = (i + 1) % all.length; else if(e.key === 'ArrowLeft') j = (i - 1 + all.length) % all.length;
    else if(e.key === 'Home') j = 0; else if(e.key === 'End') j = all.length - 1;
    if(j < 0) return; e.preventDefault(); ldSelect(all[j]); all[j].focus();
  });
  function wireAll(){ document.querySelectorAll('.v9-hub').forEach(wire); }
  window.addEventListener('resize', wireAll);
  window.addEventListener('hashchange', function(){ setTimeout(wireAll, 60); setTimeout(wireAll, 400); });
  if('ResizeObserver' in window){ var ro = new ResizeObserver(wireAll); document.querySelectorAll('.v9-hub-stage').forEach(function(s){ ro.observe(s); }); }
  if(document.readyState !== 'loading') wireAll(); else document.addEventListener('DOMContentLoaded', wireAll);
})();
</script>
'''
