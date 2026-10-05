"""Native flowcharts for the V7 manual — one visual language for every diagram.

Everything is plain HTML/CSS (plus one hand-drawn SVG for the decision chart), styled by flow.css.
Only wording that is in the docx — or printed inside the docx's own pictures — is used.

Language: white nodes with a coloured top band and a numbered ring badge, chunky coloured arrows
between nodes, snake layout where the Word table snakes (→ ↓ ←), YES/NO labels on decisions.
Colours come from one muted palette (SEQ) used everywhere; RMS steps keep Word's orange.
"""
import html
import re

esc = lambda s: html.escape(s, quote=False)

# muted, dark enough for white text (all ≥ 4.5:1)
NAVY, BLUE, TEAL, GREEN, BRONZE, BRICK, PLUM = '#1F3A5F', '#2F5D8C', '#2E7D7A', '#3F6B3A', '#8F6A1F', '#A8493E', '#6C4E96'
GOLD = '#9A6B0A'
SEQ = [NAVY, BLUE, TEAL, GREEN, BRONZE, BRICK, PLUM]
ROW_SEQ = [BLUE, TEAL, PLUM, BRONZE, GREEN, BRICK]


def _dirs(nodes):
    out = []
    for a, b in zip(nodes, nodes[1:]):
        out.append(('r' if b['col'] > a['col'] else 'l') if a['row'] == b['row'] else 'd')
    out.append(None)
    return out


def _chips(items, cls):
    return ''.join(f'<span class="{cls}">{esc(x)}</span>' for x in items)


# ───────────── snake of numbered steps (all Word flow tables) ─────────────
def snake(nodes):
    """nodes: dicts {num, when[], body[], who[], rms, row, col} in reading order."""
    cols = max(n['col'] for n in nodes)
    dirs = _dirs(nodes)
    parts = []
    for n, d in zip(nodes, dirs):
        color = GOLD
        cls = 'fx-node' + (f' fx-to-{d}' if d else '') + (' fx-rms' if n.get('rms') else '')
        inner = f'<span class="fx-badge">{esc(n["num"])}</span>'
        if n['when']:
            inner += f'<span class="fx-when">{esc(" ".join(n["when"]))}</span>'
        inner += f'<p class="fx-text">{esc(" ".join(n["body"]))}</p>'
        if n['who']:
            inner += '<span class="fx-whos">' + _chips(n['who'], 'fx-who') + '</span>'
        parts.append(f'<div class="{cls}" style="--c:{color};grid-area:{n["row"]}/{n["col"]}">{inner}</div>')
    return f'<div class="fx-flow" style="--cols:{cols}">' + ''.join(parts) + '</div>'


# ───────────── 6.3: eight cards on the same snake, each with its own colour ─────────────
CARD_COLORS = [BLUE, BRONZE, TEAL, GREEN, PLUM, PLUM, PLUM, BRICK]
CARD_POS = [(1, 1), (1, 2), (1, 3), (2, 3), (2, 2), (2, 1), (3, 1), (3, 2)]


def _bullets(items):
    groups = []
    for t in items:
        if re.match(r'^\d+\.\s', t) and groups:     # "1. Product, Process …" belongs under "Inputs for"
            groups[-1][1].append(t)
        else:
            groups.append((t, []))
    out = ''
    for t, subs in groups:
        li = esc(t)
        if subs:
            li += '<ul class="fx-sub">' + ''.join(f'<li>{esc(x)}</li>' for x in subs) + '</ul>'
        out += f'<li>{li}</li>'
    return '<ul class="fx-list">' + out + '</ul>'


def module_snake(title, cards):
    assert len(cards) == 8
    nodes = [{'row': r, 'col': c} for r, c in CARD_POS]
    dirs = _dirs(nodes)
    parts = []
    for i, ((head, bullets), (r, c), color, d) in enumerate(zip(cards, CARD_POS, CARD_COLORS, dirs)):
        cls = 'fx-node fx-card' + (f' fx-to-{d}' if d else '')
        parts.append(f'<div class="{cls}" style="--c:{color};grid-area:{r}/{c}">'
                     f'<div class="fx-head"><span class="fx-title">{esc(head)}</span><span class="fx-n">{i + 1:02d}</span></div>'
                     f'{_bullets(bullets)}</div>')
    return (f'<figure class="fx-fig"><figcaption class="fx-banner">{esc(title)}</figcaption>'
            f'<div class="fx-flow" style="--cols:3">' + ''.join(parts) + '</div></figure>')


# ───────────── 6.2 TMS: vertical process with ringed numbers on a spine ─────────────
def vlist(title, steps):
    lis = []
    for i, (head, body) in enumerate(steps):
        c = SEQ[i % len(SEQ)]
        last = ' fx-last' if i == len(steps) - 1 else ''
        lis.append(f'<li class="fx-vstep{last}" style="--c:{c}"><span class="fx-badge">{i + 1}</span>'
                   f'<div class="fx-vcard"><h5 class="fx-vhead">{esc(head)}</h5><p class="fx-text">{esc(body)}</p></div></li>')
    return (f'<figure class="fx-fig fx-vfig"><figcaption class="fx-banner fx-banner-pill">{esc(title)}</figcaption>'
            f'<ol class="fx-vlist">' + ''.join(lis) + '</ol></figure>')


# ───────────── 6.1 learner journey ─────────────
TROPHY = ('<svg class="fx-trophy" viewBox="0 0 56 56" aria-hidden="true"><path d="M16 8h24v12c0 9-5 15-12 15S16 29 16 20V8z" fill="#C9962B"/>'
          '<path d="M16 12H8v4c0 6 4 10 9 11M40 12h8v4c0 6-4 10-9 11" fill="none" stroke="#C9962B" stroke-width="3" stroke-linecap="round"/>'
          '<path d="M25 35h6v8h-6z" fill="#B8851F"/><path d="M18 43h20v6H18z" fill="#A9781B"/></svg>')


def learner_journey(cards):
    out = []
    for c in cards:
        steps, chips = c['steps'], c['chips']
        trophy = len(chips) == len(steps)
        track = []
        for i, (head, body) in enumerate(steps):
            alt = ' fx-lj-alt' if (i == len(steps) - 1 and not trophy) else ''
            track.append(f'<div class="fx-lj-step{alt}"><div class="fx-lj-head">{esc(head)}</div><div class="fx-lj-body">{esc(body)}</div></div>')
            if i < len(steps) - 1:
                track.append(f'<div class="fx-lj-link"><span class="fx-lj-label">{esc(chips[i])}</span><span class="fx-arrow"></span></div>')
        if trophy:
            track.append(f'<div class="fx-lj-link fx-lj-end"><span class="fx-lj-label">{esc(chips[-1])}</span>{TROPHY}</div>')
        out.append(f'<section class="fx-lj-card"><h4 class="fx-lj-title">{esc(c["title"])}</h4>'
                   f'<p class="fx-lj-sub">{esc(c["subtitle"])}</p><div class="fx-lj-track">' + ''.join(track) + '</div></section>')
    return '<div class="fx-lj">' + ''.join(out) + '</div>'


# ───────────── Unified Apps tree ─────────────
APP_COLORS = [BLUE, TEAL, PLUM, BRONZE, GREEN]


def unified(root, apps):
    items = []
    for i, a in enumerate(apps):
        m = re.match(r'^(.*?)\s*(\([A-Z]+\))$', a)
        c = APP_COLORS[i % len(APP_COLORS)]
        if m:
            items.append(f'<li class="v7-app" style="--c:{c}"><span class="v7-app-name">{esc(m.group(1))}</span> '
                         f'<span class="v7-app-code">{esc(m.group(2))}</span></li>')
        else:
            items.append(f'<li class="v7-app v7-app-solo" style="--c:{c}"><span class="v7-app-code">{esc(a)}</span></li>')
    return (f'<figure class="v7-apps"><div class="v7-apps-root">{esc(root)}</div>'
            f'<ol class="v7-apps-row">{"".join(items)}</ol></figure>')


# ───────────── 6.4 absenteeism: decision flowchart (hand-drawn SVG + phone list) ─────────────
ABS = {
    'start': 'Participant Unable to Attend Training Session',
    'q1': 'Did the Participant Inform in Advance?',
    'y': ['Informs Reporting Manager & IDT at least 2 days in advance (except emergencies)',
          'Reason for Absenteeism is Documented', 'Participant Scheduled for the Next Session'],
    'n': 'Absent Without Prior Intimation',
    'q2': 'Was the Reason Genuine?',
    'n_yes': 'Given a Chance to Attend the Next Scheduled Session',
    'n_no': 'Repeated absence treated as a Breach of Discipline → Reported to HR & Reporting Manager',
}


def _wrap(text, maxc):
    lines, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > maxc:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return lines + [cur]


def _label(cx, cy, text, fill, size=14, weight=700, lh=18):
    lines = _wrap(text, 99) if isinstance(text, str) else text
    y0 = cy - (len(lines) - 1) * lh / 2 + size * 0.36
    tsp = ''.join(f'<tspan x="{cx}" y="{y0 + i * lh:.1f}">{esc(t)}</tspan>' for i, t in enumerate(lines))
    return f'<text text-anchor="middle" font-size="{size}" font-weight="{weight}" fill="{fill}">{tsp}</text>'


def _box(cx, top, w, h, text, fill, maxc, fg='#fff', rx=12, weight=600):
    return (f'<rect x="{cx - w / 2}" y="{top}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>'
            + _label(cx, top + h / 2, _wrap(text, maxc), fg, weight=weight))


def _diamond(cx, cy, hw, hh, text, maxc=20):
    pts = f'{cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh} {cx - hw},{cy}'
    return (f'<polygon points="{pts}" fill="#E8C45A" stroke="#B8962E" stroke-width="1.5"/>'
            + _label(cx, cy, _wrap(text, maxc), '#1d1d1f'))


def absent_flow():
    A = ABS
    ink = '#3a3a40'
    s = [f'<defs><marker id="fxAr" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
         f'<path d="M1 1 9 5 1 9z" fill="{ink}"/></marker></defs>']
    line = lambda pts: s.append(f'<polyline points="{pts}" fill="none" stroke="{ink}" stroke-width="2.4" stroke-linejoin="round" marker-end="url(#fxAr)"/>')
    xL, xC, xR = 150, 520, 900
    # start + decision 1
    s.append(f'<rect x="{xC - 240}" y="8" width="480" height="58" rx="29" fill="{NAVY}"/>' + _label(xC, 37, A['start'], '#fff', size=15))
    line(f'{xC},68 {xC},106')
    s.append(_diamond(xC, 176, 205, 70, A['q1']))
    # YES branch (left)
    line(f'{xC - 205},176 {xL},176 {xL},306')
    s.append(f'<text x="{(xC - 205 + xL) / 2}" y="164" text-anchor="middle" font-size="14" font-weight="800" fill="{BLUE}">YES</text>')
    ys = [(306, 86, 34), (432, 62, 29), (534, 62, 29)]
    for (top, h, mc), t in zip(ys, A['y']):
        s.append(_box(xL, top, 292, h, t, BLUE, mc))
    line(f'{xL},{306 + 86 + 2} {xL},430')
    line(f'{xL},{432 + 62 + 2} {xL},532')
    # NO branch (right)
    line(f'{xC + 205},176 {xR},176 {xR},306')
    s.append(f'<text x="{(xC + 205 + xR) / 2}" y="164" text-anchor="middle" font-size="14" font-weight="800" fill="{BRICK}">NO</text>')
    s.append(_box(xR, 306, 300, 62, A['n'], BRICK, 34))
    line(f'{xR},370 {xR},408')
    s.append(_diamond(xR, 478, 150, 70, A['q2'], 16))
    line(f'{xR - 150},478 690,478 690,618')
    s.append(f'<text x="716" y="466" text-anchor="middle" font-size="14" font-weight="800" fill="{BLUE}">YES</text>')
    line(f'{xR + 150},478 1068,478 1068,618')
    s.append(f'<text x="1048" y="466" text-anchor="middle" font-size="14" font-weight="800" fill="{BRICK}">NO</text>')
    s.append(_box(690, 620, 250, 82, A['n_yes'], BRICK, 28))
    s.append(_box(1068, 620, 264, 98, A['n_no'], BRICK, 31))
    svg = (f'<svg viewBox="0 0 1200 730" role="img" aria-label="Flowchart: what happens when a participant cannot attend a training session. '
           f'If they informed in advance, the absence is documented and they are scheduled for the next session. '
           f'If not, the reason is checked: a genuine reason earns another chance; otherwise it is reported as a breach of discipline." '
           f'font-family="inherit">' + ''.join(s) + '</svg>')

    node = lambda t, cls: f'<div class="fx-dm-node {cls}">{esc(t)}</div>'
    arrow = '<span class="fx-arrow"></span>'
    yes = ''.join((arrow if i else '') + node(t, 'fx-b') for i, t in enumerate(A['y']))
    phone = (f'<div class="fx-dm fx-phone">{node(A["start"], "fx-s")}{arrow}<div class="fx-dm-q">{esc(A["q1"])}</div>'
             f'<section class="fx-dm-b"><span class="fx-dm-tag fx-yes">YES</span>{yes}</section>'
             f'<section class="fx-dm-b"><span class="fx-dm-tag fx-no">NO</span>{node(A["n"], "fx-r")}{arrow}'
             f'<div class="fx-dm-q">{esc(A["q2"])}</div>'
             f'<div class="fx-dm-sub"><span class="fx-dm-tag fx-yes">YES</span>{node(A["n_yes"], "fx-r")}</div>'
             f'<div class="fx-dm-sub"><span class="fx-dm-tag fx-no">NO</span>{node(A["n_no"], "fx-r")}</div></section></div>')
    return f'<figure class="fx-fig fx-dfig"><div class="fx-desk">{svg}</div>{phone}</figure>'


# ───────────── remaining diagrams, same language ─────────────
def _node(i, color, inner, cls='', area=''):
    return f'<div class="fx-node {cls}" style="--c:{color}{area}"><span class="fx-badge">{i}</span>{inner}</div>'


def chevrons(steps):
    """6.5 LMS: Publish → Assign → Learn → Assess → Track as an arrow band over description cards."""
    heads, bodies = [], []
    for i, (name, text) in enumerate(steps):
        c = SEQ[(i + 1) % len(SEQ)]
        heads.append(f'<li class="fx-chev-step" style="--c:{c}"><div class="fx-chev-head"><span class="fx-chev-n">{i + 1}</span>{esc(name)}</div>'
                     f'<p class="fx-text">{esc(text)}</p></li>')
    return f'<figure class="fx-fig"><ol class="fx-chev">' + ''.join(heads) + '</ol></figure>'


def ring(title, groups):
    """6.7: what IDT reports — a hub with two reporting groups."""
    cards = []
    for i, (head, lines) in enumerate(groups):
        c = [BLUE, TEAL][i % 2]
        cards.append(f'<div class="fx-node fx-hubcard" style="--c:{c}"><h5 class="fx-vhead">{esc(head)}</h5><ul class="fx-list">'
                     + ''.join(f'<li>{esc(x)}</li>' for x in lines) + '</ul></div>')
    return (f'<figure class="fx-fig fx-hubfig"><div class="fx-hub"><span>{esc(" ".join(title))}</span></div>'
            f'<div class="fx-hubcards">' + ''.join(cards) + '</div></figure>')


def smart(rows):
    nodes = []
    for i, (letter, word, desc) in enumerate(rows):
        c = SEQ[(i + 1) % len(SEQ)]
        d = ' fx-to-r' if i < len(rows) - 1 else ''
        nodes.append(f'<div class="fx-node fx-letter{d}" style="--c:{c}"><span class="fx-big">{esc(letter)}</span>'
                     f'<h5 class="fx-vhead">{esc(word)}</h5><p class="fx-text">{esc(desc)}</p></div>')
    return f'<figure class="fx-fig"><div class="fx-flow" style="--cols:{len(rows)}">' + ''.join(nodes) + '</div></figure>'


def review(items):
    cs = [BLUE, TEAL, PLUM, BRONZE, GREEN, BRICK]
    nodes = [_node(f'{i + 1:02d}', cs[i % 6], f'<p class="fx-text">{esc(t)}</p>') for i, t in enumerate(items)]
    return f'<figure class="fx-fig"><div class="fx-flow fx-plain" style="--cols:{min(len(items), 4)}">' + ''.join(nodes) + '</div></figure>'


STAR = ('<svg class="fx-star" viewBox="0 0 60 58" aria-hidden="true"><path d="M30 3l8.2 17 18.6 2.4-13.7 12.8 3.5 18.4L30 44.5 13.4 53.6l3.5-18.4L3.2 22.4 21.8 20z" '
        'fill="#C9962B" stroke="#B8851F" stroke-width="2" stroke-linejoin="round"/></svg>')


def spot(items, word):
    cs = [BLUE, TEAL, PLUM, BRONZE]
    nodes = [_node(f'{i + 1:02d}', cs[i % 4], f'<p class="fx-text">{esc(t)}</p>') for i, t in enumerate(items)]
    return (f'<figure class="fx-fig fx-spot"><div class="fx-spot-hub">{STAR}<span>{esc(word)}</span></div>'
            f'<div class="fx-spot-row" style="--n:{len(items)}">' + ''.join(nodes) + '</div></figure>')


def cycle(items, title):
    pos = [(1, 1, 'r'), (1, 2, 'd'), (2, 2, 'l'), (2, 1, 'u')]
    cs = [BLUE, TEAL, PLUM, BRONZE]
    nodes = [_node(i + 1, cs[i], f'<p class="fx-text">{esc(t)}</p>', f'fx-to-{d}', f';grid-area:{r}/{c}')
             for i, (t, (r, c, d)) in enumerate(zip(items, pos))]
    return (f'<figure class="fx-fig"><figcaption class="fx-banner fx-banner-pill">{esc(title)}</figcaption>'
            f'<div class="fx-flow" style="--cols:2;max-width:760px">' + ''.join(nodes) + '</div></figure>')
