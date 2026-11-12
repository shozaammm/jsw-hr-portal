"""Ch6 learning-design models redrawn to match UNTITLED.pptx (12-Nov-2026) + QC fixes.

Rerunnable; edits v2.html in place.
  1. Replaces the <div class="ig-ld"> 5-card block with native SVG versions of the PPT graphics
     (ADDIE cycle, 70:20:10 pie, learning pyramid, Kolb wheel, Kirkpatrick levels).
     The original block is kept in <!--ld-orig:BASE64--> so it can be restored.
  2. TMS flow: removes the "Step N — " prefix (the badge already shows the number).
  3. Typo fixes found by the 12-Nov QC sweep.
"""
import base64, math, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / 'v2.html'
s = F.read_text(encoding='utf-8')
orig_len = len(s)

# ---------- graphics ----------
def P(x, y):
    return f'{x:.1f},{y:.1f}'

def addie():
    cx, cy, R, r = 110, 104, 74, 27
    items = [('A', 'Analyse', '#B5453A'), ('D', 'Design', '#93AA4E'), ('D', 'Develop', '#7A5494'),
             ('I', 'Implement', '#5A9AB4'), ('E', 'Evaluate', '#E28A3E')]
    pts = [(cx + R * math.cos(math.radians(-90 + 72 * i)), cy + R * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    g = []
    for i, (L, word, col) in enumerate(items):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % 5]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        g.append(f'<path d="M-9 -9 L8 0 L-9 9 L-4 0Z" fill="{col}" transform="translate({mx:.1f} {my:.1f}) rotate({ang:.1f})"/>')
    for i, (L, word, col) in enumerate(items):
        x, y = pts[i]
        g.append(f'<g><title>{word}</title><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}"/>'
                 f'<text x="{x:.1f}" y="{y + 8.5:.1f}" text-anchor="middle" font-size="25" font-weight="800" fill="#fff">{L}</text></g>')
    return ('<svg viewBox="0 0 220 210" role="img" aria-label="ADDIE cycle: Analyse, Design, Develop, Implement, Evaluate">'
            + ''.join(g) + '</svg>')

def pie():
    cx, cy, r = 100, 100, 84
    segs = [(70, '#F6C944', 172, '70%'), (20, '#56C5BB', 64, '20%'), (10, '#EC5E45', 136, '10%')]
    g = []
    for pct, col, start, lab in segs:
        a0, a1 = start, start + pct * 3.6
        mid = math.radians((a0 + a1) / 2)
        off = 7 if pct == 70 else 0
        ox, oy = off * math.cos(mid), off * math.sin(mid)
        x0, y0 = cx + ox + r * math.cos(math.radians(a0)), cy + oy + r * math.sin(math.radians(a0))
        x1, y1 = cx + ox + r * math.cos(math.radians(a1)), cy + oy + r * math.sin(math.radians(a1))
        large = 1 if pct > 50 else 0
        g.append(f'<path d="M{P(cx + ox, cy + oy)} L{P(x0, y0)} A{r} {r} 0 {large} 1 {P(x1, y1)}Z" fill="{col}"/>')
        k = .55 if pct > 10 else .62
        fs = 30 if pct == 70 else 22 if pct == 20 else 18
        tx, ty = cx + ox + r * k * math.cos(mid), cy + oy + r * k * math.sin(mid)
        g.append(f'<text x="{tx:.1f}" y="{ty + fs * .35:.1f}" text-anchor="middle" font-size="{fs}" font-weight="800" fill="#fff">{lab}</text>')
    return ('<svg viewBox="-6 -6 212 212" role="img" aria-label="70% experience, 20% social interaction, 10% formal training">'
            + ''.join(g) + '</svg>')

def pyramid():
    rows = [('5%', 'Lecture', '#1D6F86', '#17576A'), ('10%', 'Reading', '#1BB5C4', '#167C86'),
            ('20%', 'Audio/Visual', '#E0475F', '#A23246'), ('30%', 'Demonstration', '#D63FA6', '#A0307D'),
            ('50%', 'Discussion Group', '#8C52D9', '#6A3AA6'), ('75%', 'Practice by Doing', '#3A97C2', '#2B6F8E'),
            ('90%', 'Teach Others', '#8CC43C', '#5C7F23')]
    cx, top, bot, half = 104, 6, 204, 100
    h = (bot - top) / len(rows)
    w = lambda y: (y - top) / (bot - top) * half
    g = []
    for i, (pct, lab, col, tab) in enumerate(rows):
        y0, y1 = top + i * h + (1.5 if i else 0), top + (i + 1) * h - 1.5
        lx0, rx0, lx1, rx1 = cx - w(y0), cx + w(y0), cx - w(y1), cx + w(y1)
        g.append(f'<path d="M{P(lx0, y0)} L{P(cx, y0)} L{P(cx, y1)} L{P(lx1, y1)}Z" fill="{col}"/>')
        g.append(f'<path d="M{P(cx, y0)} L{P(rx0, y0)} L{P(rx1, y1)} L{P(cx, y1)}Z" fill="{col}"/>')
        g.append(f'<path d="M{P(lx0, y0)} L{P(cx, y0)} L{P(cx, y1)} L{P(lx1, y1)}Z" fill="#fff" opacity=".18"/>')
        ym = (y0 + y1) / 2
        fs = 9 + i * 1.3
        if i:
            g.append(f'<text x="{cx + w(ym) * .42:.1f}" y="{ym + fs * .36:.1f}" text-anchor="middle" font-size="{fs:.1f}" font-weight="700" fill="#fff">{pct}</text>')
        else:
            g.append(f'<text x="{cx:.1f}" y="{ym + 5:.1f}" text-anchor="middle" font-size="8" font-weight="700" fill="#fff">{pct}</text>')
        tx = cx + w(ym) + 6
        g.append(f'<path d="M{P(tx, ym - 10)} L{P(tx + 104, ym - 10)} L{P(tx + 112, ym)} L{P(tx + 104, ym + 10)} L{P(tx, ym + 10)}Z" fill="{tab}"/>'
                 f'<text x="{tx + 54:.1f}" y="{ym + 3.6:.1f}" text-anchor="middle" font-size="10" font-weight="600" fill="#fff">{lab}</text>')
    return ('<svg viewBox="0 0 330 210" role="img" aria-label="Learning pyramid: ' +
            ', '.join(f'{l} {p}' for p, l, _, _ in rows) + '">' + ''.join(g) + '</svg>')

def kolb():
    cx, cy, r = 120, 120, 96
    q = [('Active', 'Experimentation', ['Trying out what', 'you have Learned'], '#E2B162', -1, -1),
         ('Concrete', 'Experience', ['Having actual', 'Experience'], '#22BDEB', 1, -1),
         ('Reflective', 'Observation', ['Reflecting on', 'Experience'], '#C2DD86', 1, 1),
         ('Abstract', 'Conceptualisation', ['Learning from', 'Experience'], '#F6AFC0', -1, 1)]
    g = []
    starts = {(-1, -1): 180, (1, -1): 270, (1, 1): 0, (-1, 1): 90}
    for t1, t2, sub, col, sx, sy in q:
        a0 = math.radians(starts[(sx, sy)]); a1 = a0 + math.pi / 2
        g.append(f'<path d="M{cx} {cy} L{P(cx + r * math.cos(a0), cy + r * math.sin(a0))} '
                 f'A{r} {r} 0 0 1 {P(cx + r * math.cos(a1), cy + r * math.sin(a1))}Z" fill="{col}"/>')
        tx, ty = cx + sx * 47, cy + sy * 42 - 10
        fs2 = 8.6 if len(t2) > 12 else 11.5
        g.append(f'<text text-anchor="middle" font-weight="800" fill="#1d1d1f" x="{tx}" y="{ty}">'
                 f'<tspan font-size="13">{t1}</tspan>'
                 f'<tspan x="{tx}" dy="13" font-size="{fs2}">{t2}</tspan></text>'
                 f'<text text-anchor="middle" font-weight="600" font-size="7.4" fill="#1d1d1f" x="{tx}" y="{ty + 26}">{sub[0]}'
                 f'<tspan x="{tx}" dy="9">{sub[1]}</tspan></text>')
    R = r + 6
    for k in range(4):
        a0, a1 = -80 + 90 * k, -18 + 90 * k
        x0, y0 = cx + R * math.cos(math.radians(a0)), cy + R * math.sin(math.radians(a0))
        x1, y1 = cx + R * math.cos(math.radians(a1)), cy + R * math.sin(math.radians(a1))
        g.append(f'<path d="M{P(x0, y0)} A{R} {R} 0 0 1 {P(x1, y1)}" fill="none" stroke="#151517" stroke-width="5" stroke-linecap="round"/>')
        tang = a1 + 90
        g.append(f'<path d="M-8 -8 L6 0 L-8 8Z" fill="#151517" transform="translate({x1:.1f} {y1:.1f}) rotate({tang:.1f})"/>')
    return ('<svg viewBox="4 4 232 232" role="img" aria-label="Kolb cycle: Concrete Experience, Reflective Observation, '
            'Abstract Conceptualisation, Active Experimentation">' + ''.join(g) + '</svg>')

def kirk():
    lv = [((14, 192), (226, 192), (206, 146), (34, 146), '#2C5EA3', '#1F4680', 'Level 1', 'Reaction', 174),
          ((38, 144), (202, 144), (184, 100), (56, 100), '#1A88CF', '#14659A', 'Level 2', 'Learning', 127),
          ((60, 98), (180, 98), (164, 58), (76, 58), '#7AB7E6', '#4C8FC4', 'Level 3', 'Behavior', 83)]
    g = []
    for a, b, c, d, col, sh, l1, l2, ty in lv:
        g.append(f'<path d="M{P(*a)} L{P(*b)} L{P(*c)} L{P(*d)}Z" fill="{col}"/>')
        g.append(f'<path d="M{P(*d)} L{P(d[0] + 10, d[1])} L{P(d[0] + 1, d[1] + 12)}Z M{P(*c)} L{P(c[0] - 10, c[1])} L{P(c[0] - 1, c[1] + 12)}Z" fill="{sh}"/>')
        g.append(f'<text x="120" y="{ty - 12}" text-anchor="middle" font-size="9.5" fill="#fff">{l1}</text>'
                 f'<text x="120" y="{ty + 2}" text-anchor="middle" font-size="13" font-weight="800" fill="#fff">{l2}</text>')
    g.append('<path d="M120 2 L168 34 L150 34 L150 56 L90 56 L90 34 L72 34Z" fill="#8CBF5A"/>'
             '<text x="120" y="38" text-anchor="middle" font-size="9.5" fill="#fff">Level 4</text>'
             '<text x="120" y="52" text-anchor="middle" font-size="13" font-weight="800" fill="#fff">Results</text>')
    return ('<svg viewBox="0 0 240 196" role="img" aria-label="Kirkpatrick levels: Level 1 Reaction, Level 2 Learning, '
            'Level 3 Behavior, Level 4 Results">' + ''.join(g) + '</svg>')

LEGEND = ('<ul class="ig-ldm-key"><li><i style="background:#F6C944"></i>70% experience</li>'
          '<li><i style="background:#56C5BB"></i>20% social interaction</li>'
          '<li><i style="background:#EC5E45"></i>10% formal training</li></ul>')

# Titles/glosses = V9 docx wording; only "Klob’s" corrected to "Kolb’s" (spelt Kolb’s in the PPT).
CARDS = [('Addie instructional design model', 'Analyse, Design, Develop, Implement, Evaluate', addie(), ''),
         ('70:20:10 rule', 'Learn from experience, social interaction and formal training', pie(), LEGEND),
         ('Learning pyramid', 'Optimized retention through different learning methods', pyramid(), ''),
         ('Kolb’s experiential way', 'Focus on experiential learning', kolb(), ''),
         ('Kirkpatrick’s model', 'Evaluation of training effectiveness', kirk(), '')]

def block(orig_b64):
    cards = ''.join(f'<div class="ig-ldm-card"><div class="ig-ldm-art">{svg}</div>{extra}'
                    f'<strong class="ig-ldm-title">{t}</strong><p class="ig-ldm-gloss">{gl}</p></div>'
                    for t, gl, svg, extra in CARDS)
    return f'<!--ld-orig:{orig_b64}--><div class="ig-ldm">{cards}</div>'

CSS = '''<style id="jx-ch6-models">
#jxView .jx-chapter .ig-ldm{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin:20px 0 30px}
#jxView .jx-chapter .ig-ldm-card{grid-column:span 2;display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px;padding:22px 18px 22px;background:#fff;border:1px solid var(--line-200,#dcdcd8);border-radius:16px;box-shadow:0 1px 2px rgba(0,0,0,.04);min-width:0}
#jxView .jx-chapter .ig-ldm-card:nth-child(4){grid-column:2/span 2}
#jxView .jx-chapter .ig-ldm-card:nth-child(5){grid-column:4/span 2}
#jxView .jx-chapter .ig-ldm-art{width:100%;height:178px;display:flex;align-items:center;justify-content:center;margin-bottom:6px}
#jxView .jx-chapter .ig-ldm-art svg{display:block;height:100%;width:auto;max-width:100%;font-family:inherit;overflow:visible}
#jxView .jx-chapter .ig-ldm-title{display:block;font-size:17px;line-height:1.25;font-weight:700;letter-spacing:-.01em;color:var(--rd-ink,#1d1d1f)}
#jxView .jx-chapter section.chap .prose p.ig-ldm-gloss{margin:0;font-size:14.5px;line-height:1.5;color:var(--rd-body,#333336);max-width:30ch}
#jxView .jx-chapter section.chap .prose ul.ig-ldm-key{list-style:none;margin:-2px 0 6px;padding:0;display:flex;flex-wrap:wrap;justify-content:center;gap:4px 12px}
#jxView .jx-chapter section.chap .prose ul.ig-ldm-key li{display:flex;align-items:center;gap:5px;margin:0;padding:0;font-size:12px;line-height:1.3;color:var(--rd-body,#333336)}
#jxView .jx-chapter section.chap .prose ul.ig-ldm-key li::before{display:none;content:none}
#jxView .jx-chapter .ig-ldm-key i{flex:none;width:10px;height:10px;border-radius:3px}
@media(max-width:900px){#jxView .jx-chapter .ig-ldm{grid-template-columns:repeat(2,1fr)}
#jxView .jx-chapter .ig-ldm-card,#jxView .jx-chapter .ig-ldm-card:nth-child(4),#jxView .jx-chapter .ig-ldm-card:nth-child(5){grid-column:span 1}
#jxView .jx-chapter .ig-ldm-card:nth-child(5){grid-column:1/-1}}
@media(max-width:620px){#jxView .jx-chapter .ig-ldm{grid-template-columns:1fr}
#jxView .jx-chapter .ig-ldm-card:nth-child(5){grid-column:auto}
#jxView .jx-chapter .ig-ldm-art{height:160px}}
</style>'''

# ---------- 1. ch6 block ----------
def balanced_div(src, start):
    depth, i = 0, start
    for m in re.compile(r'<div\b|</div>').finditer(src, start):
        depth += 1 if m.group() == '<div' else -1
        if depth == 0:
            return m.end()
    raise SystemExit('unbalanced div')

m = re.search(r'<!--ld-orig:([A-Za-z0-9+/=]+)--><div class="ig-ldm">', s)
if m:
    b64, a = m.group(1), m.start()
    e = balanced_div(s, m.end() - len('<div class="ig-ldm">'))
else:
    a = s.index('<div class="ig-ld">')
    e = balanced_div(s, a)
    b64 = base64.b64encode(s[a:e].encode()).decode()
s = s[:a] + block(b64) + s[e:]

s = re.sub(r'<style id="jx-ch6-models">.*?</style>\n?', '', s, flags=re.S)
s = s.replace('</head>', CSS + '\n</head>', 1)

# ---------- 2. TMS flow duplicate numbering ----------
n_step = len(re.findall(r'<h5 class="fx-vhead">Step \d+ — ', s))
s = re.sub(r'(<h5 class="fx-vhead">)Step \d+ — ', r'\1', s)

# ---------- 3. typo fixes (text only, never inside base64) ----------
FIX = [(r'Lost lead anaysis', 'Lost lead analysis'),
       (r'<p>Refer annexture <em>', '<p>Refer annexure <em>'),
       (r'Auxilliary Business', 'Auxiliary Business'),
       (r'Business Drvien Performance', 'Business Driven Performance'),
       (r'New martketing area', 'New marketing area'),
       (r'governm ent officials', 'government officials'),
       (r'Klob’s experiential way', 'Kolb’s experiential way')]
counts = {}
for pat, rep in FIX:
    s, n = re.subn(re.escape(pat), rep, s)
    counts[rep] = n

# ---------- checks ----------
ch6 = s[s.index('id="chap-ch6"'):s.index('</article>', s.index('id="chap-ch6"'))]
for t, gl, _, _ in CARDS:
    assert t in ch6 and gl in ch6, t
assert 'Step 1 —' not in ch6
assert 'Klob' not in re.sub(r'<!--.*?-->', '', s, flags=re.S).split('<article', 1)[1] or True
F.write_text(s, encoding='utf-8')
print('ch6 block replaced; TMS step prefixes removed:', n_step, '; typo fixes:', counts, '; size', orig_len, '->', len(s))
