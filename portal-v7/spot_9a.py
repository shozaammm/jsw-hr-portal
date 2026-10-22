"""9A Spot Recognition Template redesigned as a die-cut recognition card (yellow / navy, white sticker border,
hang hole, smiley badge), after the dealership's physical recognition tags. Rerunnable, applied to v2.html.
Every word is the 9A sheet's own text; underscore fill-in lines become ruled lines.

usage: python3 portal-v7/spot_9a.py [JSW_HR_Manual_Annexures-xlsx]
"""
import html, json, re, sys, warnings
from pathlib import Path
import openpyxl

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / 'v2.html'
ALL = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Downloads/JSW_HR_Manual_Annexures.xlsx'
esc = lambda s: html.escape(s, quote=False)

ws = openpyxl.load_workbook(ALL)['9A_Spot_Recognition_Template']
S = {c.coordinate: str(c.value).strip() for r in ws.iter_rows() for c in r if c.value is not None}
fills = lambda s: re.sub(r'\s*_{3,}', '', s).strip()                 # text with its underscore line removed
checks = [S[f'A{i}'] for i in range(9, 16)]
assert all(c.startswith('☐') for c in checks), checks
label = lambda c: re.sub(r'^☐\s*', '', c)

SMILEY = ('<svg class="spot-smile" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
          '<circle cx="50" cy="50" r="47" fill="#FFE04D" stroke="#fff" stroke-width="6"/>'
          '<ellipse cx="35" cy="40" rx="5.500" ry="8" fill="#1b1b1d"/><ellipse cx="65" cy="40" rx="5.500" ry="8" fill="#1b1b1d"/>'
          '<path d="M26 58 Q50 84 74 58" fill="none" stroke="#1b1b1d" stroke-width="5" stroke-linecap="round"/></svg>')

field = lambda k, v: f'<div class="spot-f"><span>{esc(S[k])}</span><i></i></div>'
other = checks[-1]
items = ''.join(f'<li><b></b><span>{esc(label(c))}</span></li>' for c in checks[:-1])
items += f'<li><b></b><span>{esc(fills(label(other)))}</span><i></i></li>'
lines = '<i></i>' * 4
who = ''.join(f'<div class="spot-by"><span>{esc(fills(S[k]))}</span><i></i></div>' for k in ('B14', 'B15', 'B16'))

CARD = (
    '<div class="spot-wrap"><div class="spot"><div class="spot-hole"></div><div class="spot-card">'
    f'<div class="spot-top">{SMILEY}<div><div class="spot-org">{esc(S["A2"])}</div>'
    f'<h2 class="spot-title">{esc(S["A1"])}</h2></div></div>'
    f'<p class="spot-tag">{esc(S["A3"])}</p>'
    '<div class="spot-panel">'
    f'<div class="spot-fields">{field("A5", "A6")}{field("B5", "B6")}{field("C5", "C6")}</div>'
    '<div class="spot-cols">'
    f'<div><h4>{esc(S["A8"])}</h4><ul class="spot-checks">{items}</ul></div>'
    f'<div><h4>{esc(S["B8"])}</h4><div class="spot-lines">{lines}</div>'
    f'<h4 class="spot-awd">{esc(S["B13"])}</h4>{who}</div>'
    '</div></div>'
    f'<div class="spot-foot">{esc(S["A18"])}</div>'
    '</div></div></div>')

CSS = '''<style id="jx-spot-css">
.spot-wrap{container-type:inline-size;max-width:540px;margin:6px auto 14px;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.spot{position:relative;background:#fff;border-radius:11cqw 11cqw 8cqw 8cqw;padding:2.6cqw;box-shadow:0 1cqw 3.5cqw rgba(0,0,0,.28),0 0 0 .35cqw #e3e3e0}
.spot-hole{position:absolute;top:2.6cqw;left:50%;width:6.5cqw;height:6.5cqw;margin-left:-3.25cqw;border-radius:50%;background:#cfcfcb;box-shadow:inset 0 .4cqw .8cqw rgba(0,0,0,.35);z-index:2}
.spot-card{background:#F9C80E;border-radius:9cqw 9cqw 6cqw 6cqw;padding:12cqw 4.5cqw 0;overflow:hidden;color:#1b1b1d}
.spot-top{display:flex;align-items:center;gap:3.5cqw}
.spot-smile{flex:0 0 auto;width:20cqw;height:20cqw;filter:drop-shadow(0 .6cqw .8cqw rgba(0,0,0,.25))}
.spot-org{display:inline-block;background:#1E2A4A;color:#fff;font-size:max(10px,2.7cqw);font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:1cqw 2.6cqw;border-radius:99px}
.spot-title{margin:1.6cqw 0 0;font-size:max(20px,8.4cqw);line-height:.98;font-weight:900;font-style:italic;text-transform:uppercase;letter-spacing:-.02em;color:#1b1b1d;border:0;padding:0}
.spot-tag{margin:3cqw 0 3.4cqw;font-size:max(12px,3.5cqw);font-style:italic;font-weight:700;color:#1E2A4A}
.spot-panel{background:#fff;border-radius:5cqw;padding:4cqw 4cqw 4.4cqw;box-shadow:0 .6cqw 0 rgba(30,42,74,.18)}
.spot-fields{display:grid;grid-template-columns:repeat(3,1fr);gap:3cqw;margin-bottom:4cqw}
.spot-f span,.spot-by span,.spot-panel h4{display:block;font-size:max(9.5px,2.3cqw);font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#1E2A4A;margin:0}
.spot-f i,.spot-lines i,.spot-by i,.spot-checks li>i{display:block;border-bottom:.45cqw solid #1b1b1d;height:5.4cqw}
.spot-cols{display:grid;grid-template-columns:1fr 1fr;gap:4.5cqw}
.spot-panel h4{margin:0 0 2cqw}
.spot-awd{margin-top:4cqw!important}
.spot-checks{list-style:none;margin:0;padding:0;display:grid;gap:2cqw}
.spot-checks li{display:flex;align-items:center;gap:2cqw;font-size:max(11px,2.9cqw);font-weight:600;line-height:1.2}
.spot-checks b{flex:0 0 auto;width:3.4cqw;height:3.4cqw;min-width:11px;min-height:11px;border:.55cqw solid #1E2A4A;border-radius:.9cqw;background:#fff}
.spot-checks li>i{flex:1 1 6cqw;min-width:6cqw;height:3.4cqw}
.spot-lines i{height:5.8cqw}
.spot-by{display:flex;align-items:flex-end;gap:2cqw;margin-top:1.4cqw}
.spot-by span{font-size:max(10px,2.6cqw);letter-spacing:0;text-transform:none;font-weight:700;color:#1b1b1d;flex:0 0 auto}
.spot-by i{flex:1;height:4.2cqw}
.spot-foot{margin:4.5cqw -4.5cqw 0;background:#1E2A4A;color:#fff;text-align:center;font-weight:800;font-size:max(11px,3.1cqw);padding:3.6cqw 3cqw;letter-spacing:.01em}
@container (max-width:400px){.spot-cols{grid-template-columns:1fr}.spot-fields{grid-template-columns:1fr;gap:2.5cqw}}
</style>'''

h = V2.read_text(encoding='utf-8')
m = re.search(r'<script id="jx-annex-docs">window\.ANNEX_DOCS = (\{.*?\});</script>', h, re.S)
docs = json.loads(m.group(1))
old = docs['9A']['content']
use = re.match(r'\s*(<p class="annex-doc-use">.*?</p>)', old, re.S)
docs['9A']['content'] = (use.group(1) if use else '') + CARD
new_js = '<script id="jx-annex-docs">window.ANNEX_DOCS = ' + json.dumps(docs, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
h = h[:m.start()] + new_js + h[m.end():]
if 'id="jx-spot-css"' in h:
    h = re.sub(r'<style id="jx-spot-css">.*?</style>', lambda _: CSS, h, count=1, flags=re.S)
else:
    h = h.replace('<style id="jx-annex-docs-css">', CSS + '<style id="jx-annex-docs-css">', 1)
V2.write_text(h, encoding='utf-8')
print('9A redesigned; had use line:', bool(use))
