"""Chapter 6 feedback round (2026-10-22), applied to v2.html. Rerunnable.

1. Learning design techniques -> infographic (all five visible, wording unchanged except the colon that split name from gloss)
2. 6A / 6C mentions inside the flow + "What IDT reports" become links (annexure chips)
3. ordinal suffixes (20th, 1st, 3rd ...) set as superscript in chapter text
4. 6A-6C become viewable annexures: workbook sheets rendered into window.ANNEX_DOCS (same renderer as annexures.py),
   and the three download rows in ch6 + the #annexure appendix become "View File" rows

usage: python3 portal-v7/ch6_feedback.py [dir-with-6A-6B-6C-xlsx]
"""
import json, re, sys, warnings
from pathlib import Path
import openpyxl

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / 'v2.html'
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Downloads'
FILES = {'6A': '6A. Training Calendarization Template.xlsx', '6B': '6B. JSW_Training_Feedback_Form.xlsx', '6C': '6C. Monthly Training Summary.xlsx'}
TITLES = {'6A': 'Training Calendarization Template', '6B': 'Training Feedback Form', '6C': 'Monthly Training Summary'}

# reuse annexures.py's sheet renderer verbatim (everything between fmt() and the 3D picture block)
src = (ROOT / 'portal-v7/annexures.py').read_text()
chunk = src[src.index('def fmt('):src.index('# 3D is a picture')]
G = {'openpyxl': openpyxl, 're': re, 'datetime': __import__('datetime'), 'html': __import__('html'),
     'get_column_letter': openpyxl.utils.get_column_letter}
G['esc'] = lambda s: G['html'].escape(s, quote=True)
G['wb'] = openpyxl.Workbook()  # the chunk evaluates THEME once at import; real books are set per render
exec(chunk, G)


def render_book(code):
    wb = openpyxl.load_workbook(SRC / FILES[code])
    wv = openpyxl.load_workbook(SRC / FILES[code], data_only=True)
    G['wb'] = wb
    G['THEME'] = G['_theme_colors']()
    parts = []
    vis = [ws for ws in wb if ws.sheet_state == 'visible']
    for ws in vis:
        body = G['render'](ws, wv[ws.title])
        head = f'<h4 class="annex-doc-sheet">{G["esc"](ws.title)}</h4>' if len(vis) > 1 else ''
        parts.append(head + body)
    return ''.join(parts)


h = V2.read_text(encoding='utf-8')

# ---------- 4. docs ----------
m = re.search(r'<script id="jx-annex-docs">window\.ANNEX_DOCS = (\{.*?\});</script>', h, re.S)
docs = json.loads(m.group(1).replace('<\\/', '</'))
for code in FILES:
    docs[code] = {'code': code, 'title': TITLES[code],
                  'filename': f'{code}_{TITLES[code].replace(" ", "_")}.doc', 'content': render_book(code)}
docs = {k: docs[k] for k in sorted(docs, key=lambda c: (int(re.match(r'\d+', c).group()), c))}
new_js = '<script id="jx-annex-docs">window.ANNEX_DOCS = ' + json.dumps(docs, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
h = h[:m.start()] + new_js + h[m.end():]

EYE = ('<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">'
       '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>')


def item(code, with_id):
    t = f'{code}. {TITLES[code]}'
    return (f'<div{f" id=\"annex-{code}\"" if with_id else ""} class="annex-file-item" role="button" tabindex="0" '
            f'title="View {t}" onclick="openAnnexViewer(event, \'{code}\')" '
            f'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){{openAnnexViewer(event, \'{code}\')}}">'
            f'<div class="annex-file-left"><div class="annex-file-icon">📄</div>'
            f'<div class="annex-file-name">{t}</div></div>'
            f'<div class="annex-view-badge">{EYE} View File</div></div>')


def wrap(items):
    return '<!--annex-list--><div class="annex-file-list">' + items + '</div><!--/annex-list-->\n'


DL = re.compile(r'(?:<a (?:id="annex-6[ABC]" )?class="annex-file-item" href="#annexure" onclick="handleAnnexDownload\(event, \'6[ABC]\. [^\n]*?</a>\n?){3}')
hits = list(DL.finditer(h))
if hits:
    assert len(hits) == 2, len(hits)
    for mm, with_id in ((hits[1], True), (hits[0], False)):  # later one first so offsets hold
        h = h[:mm.start()] + wrap(''.join(item(c, with_id) for c in FILES)) + h[mm.end():]

# ---------- 2. links in ch6 ----------
a = h.index('<section class="chap" id="ch6">')
b = h.index('</section>', a)
sec = h[a:b]
# ---------- 1. learning design infographic ----------
ico = lambda body: ('<svg viewBox="0 0 64 40" width="64" height="40" fill="none" stroke="currentColor" stroke-width="2" '
                    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + body + '</svg>')
G_PYR = ico('<path d="M32 3 6 37h52z"/><path d="M19.500 20h25"/><path d="M12.700 29h38.600"/>')
G_KOLB = ico('<circle cx="32" cy="20" r="13"/><path d="M-2.8 -2.8 0 0 -2.8 2.8" transform="translate(41.19 10.81) rotate(45)"/><path d="M-2.8 -2.8 0 0 -2.8 2.8" transform="translate(41.19 29.19) rotate(135)"/><path d="M-2.8 -2.8 0 0 -2.8 2.8" transform="translate(22.81 29.19) rotate(225)"/><path d="M-2.8 -2.8 0 0 -2.8 2.8" transform="translate(22.81 10.81) rotate(315)"/><circle cx="32" cy="7" r="3.2" fill="currentColor"/><circle cx="45" cy="20" r="3.2" fill="currentColor"/><circle cx="32" cy="33" r="3.2" fill="currentColor"/><circle cx="19" cy="20" r="3.2" fill="currentColor"/>')
G_KIRK = ico('<rect x="6" y="27" width="10" height="10" rx="1.500"/><rect x="20" y="19" width="10" height="18" rx="1.500"/><rect x="34" y="11" width="10" height="26" rx="1.500"/><rect x="48" y="3" width="10" height="34" rx="1.500"/>')
ld_old = re.search(r'<figure class="v9-ld" data-v9="ld">.*?</figure>', sec, re.S)
if ld_old:
    def card(n, name, gloss, graphic, cls=''):
        return (f'<div class="ig-ld-card{cls}"><div class="ig-ld-head"><span class="ig-ld-n">{n}</span><strong>{name}</strong></div>'
                f'<p class="ig-ld-gloss">{gloss}</p><div class="ig-ld-art">{graphic}</div></div>')
    addie = '<ol class="ig-ld-cycle">' + ''.join(f'<li><b>{w[0]}</b><span>{w}</span></li>' for w in ['Analyse', 'Design', 'Develop', 'Implement', 'Evaluate']) + '</ol>'
    bar = ('<div class="ig-ld-bar"><div style="flex:70"><b>70</b><span>experience</span></div><div style="flex:20"><b>20</b><span>social interaction</span></div>'
           '<div style="flex:10"><b>10</b><span>formal training</span></div></div>')
    new = ('<div class="ig-ld">' +
           card(1, 'Addie instructional design model', 'Analyse, Design, Develop, Implement, Evaluate', addie, ' ig-ld-wide') +
           card(2, '70:20:10 rule', 'Learn from experience, social interaction and formal training', bar, ' ig-ld-wide') +
           card(3, 'Learning pyramid', 'Optimized retention through different learning methods', G_PYR) +
           card(4, 'Klob’s experiential way', 'Focus on experiential learning', G_KOLB) +
           card(5, 'Kirkpatrick’s model', 'Evaluation of training effectiveness', G_KIRK) + '</div>')
    sec = sec[:ld_old.start()] + new + sec[ld_old.end():]
h = h[:a] + sec + h[b:]
h = h.replace('<li>Create training calendar 6A basis to TNA inputs using form',
                  '<li>Create training calendar <a class="v7-ref" href="#annex-6A">6A</a> basis to TNA inputs using form')
h = h.replace('<li>monthly training summary 6C</li>', '<li>monthly training summary <a class="v7-ref" href="#annex-6C">6C</a></li>')

# ---------- 3. ordinals ----------
ORD = re.compile(r'\b(\d{1,2})(st|nd|rd|th)\b')
def sup(txt):
    return ORD.sub(r'\1<sup class="v7-ord">\2</sup>', txt)
starts = [m.start() for m in re.finditer(r'<section class="chap"', h)]
end_all = h.index('<!-- ============ ANNEXURE DOCUMENT VIEWER MODAL')
bounds = list(zip(starts, starts[1:] + [end_all]))
out, pos = [], 0
for st, en in bounds:  # chapters hold nested <section>s, so cut at the next chapter, not at the first </section>
    out.append(h[pos:st])
    parts = re.split(r'(<[^>]+>)', h[st:en])
    skip = 0
    for i, p in enumerate(parts):
        if p.startswith('<'):
            if p.endswith('/>'):
                continue
            if re.match(r'<(script|style|svg)\b', p): skip += 1
            elif re.match(r'</(script|style|svg)>', p): skip -= 1
            continue
        if not skip:
            parts[i] = sup(p)
    out.append(''.join(parts))
    pos = en
out.append(h[pos:])
h = ''.join(out)

# ---------- css ----------
if 'id="jx-ch6-fb-css"' not in h:
    CSS = r'''<style id="jx-ch6-fb-css">
.v7-ord{font-size:.62em;line-height:0;vertical-align:.5em;font-weight:inherit;letter-spacing:.01em;margin-left:.04em}
@media(pointer:coarse){.jx-chapter a.v7-ref{position:relative}.jx-chapter a.v7-ref::after{content:'';position:absolute;inset:-11px -7px}}
.annex-doc-sheet{margin:22px 0 8px;font-size:13px;font-weight:700;color:#1e293b}
.annex-doc-sheet:first-child{margin-top:0}

/* learning design techniques */
.jx-chapter .ig-ld{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:18px 0 28px}
.jx-chapter .ig-ld-card{grid-column:span 2;display:flex;flex-direction:column;gap:10px;padding:18px 20px 20px;background:#fff;border:1px solid var(--line-200,#dcdcd8);border-radius:16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.jx-chapter .ig-ld-wide{grid-column:span 3}
.jx-chapter .ig-ld-head{display:flex;align-items:center;gap:12px}
.jx-chapter .ig-ld-head strong{font-size:16px;line-height:1.25;font-weight:650;letter-spacing:-.01em;color:var(--rd-ink,#1d1d1f)}
.jx-chapter .ig-ld-n{flex:none;display:grid;place-items:center;width:28px;height:28px;border-radius:9px;background:#151517;color:#fff;font-size:13px;font-weight:700}
.jx-chapter section.chap .prose p.ig-ld-gloss{margin:0;font-size:14.5px;line-height:1.55;color:var(--rd-body,#333336);max-width:none}
.jx-chapter .ig-ld-art{margin-top:auto;padding-top:6px;color:#151517}
.jx-chapter .ig-ld-card:not(.ig-ld-wide) .ig-ld-art svg{display:block;width:76px;height:48px}
.jx-chapter .ig-ld-cycle{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.jx-chapter .ig-ld-cycle li{position:relative;display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center;font-size:12.5px;font-weight:650;color:var(--rd-ink,#1d1d1f);min-width:0}
.jx-chapter .ig-ld-cycle li b{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:#151517;color:#fff;font-size:15px}
.jx-chapter .ig-ld-cycle li:not(:last-child)::after{content:'';position:absolute;top:19px;left:calc(50% + 24px);right:calc(-50% + 24px);height:2px;background:#9a9a9f}
.jx-chapter .ig-ld-cycle li span{overflow-wrap:anywhere}
.jx-chapter .ig-ld-bar{display:flex;gap:4px;border-radius:10px;overflow:hidden}
.jx-chapter .ig-ld-bar div{display:flex;flex-direction:column;gap:2px;padding:10px 12px;background:#e9e9ea;min-width:84px}
.jx-chapter .ig-ld-bar div:first-child{background:#151517;color:#fff}
.jx-chapter .ig-ld-bar div:nth-child(2){background:#6c6c70;color:#fff}
.jx-chapter .ig-ld-bar b{font-size:20px;font-weight:800;line-height:1.1}
.jx-chapter .ig-ld-bar span{font-size:12px;line-height:1.25}
@media(max-width:900px){.jx-chapter .ig-ld{grid-template-columns:repeat(2,1fr)}.jx-chapter .ig-ld-card,.jx-chapter .ig-ld-wide{grid-column:span 1}.jx-chapter .ig-ld-wide{grid-column:1/-1}.jx-chapter .ig-ld-card:last-child{grid-column:1/-1}}
@media(max-width:620px){.jx-chapter .ig-ld{grid-template-columns:1fr}.jx-chapter .ig-ld-card:last-child{grid-column:auto}
.jx-chapter .ig-ld-cycle{grid-template-columns:1fr;gap:8px}.jx-chapter .ig-ld-cycle li{flex-direction:row;text-align:left;gap:12px}.jx-chapter .ig-ld-cycle li:not(:last-child)::after{display:none}
.jx-chapter .ig-ld-cycle li b{width:32px;height:32px;font-size:14px}}
</style>
'''
    h = h.replace('<style id="jx-annex-docs-css">', CSS + '<style id="jx-annex-docs-css">', 1)

V2.write_text(h, encoding='utf-8')
print('ok; docs:', len(docs))
