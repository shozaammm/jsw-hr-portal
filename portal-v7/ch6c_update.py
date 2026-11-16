"""2026-11-16: re-render annexure 6C from '6C. Monthly Training Summary 1.xlsx' into window.ANNEX_DOCS (v2.html). Rerunnable."""
import json, re, sys, warnings
from pathlib import Path
import openpyxl
warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / 'v2.html'
X = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Downloads/6C. Monthly Training Summary 1.xlsx'
src = (ROOT / 'portal-v7/annexures.py').read_text()
chunk = src[src.index('def fmt('):src.index('# 3D is a picture')]
import datetime, html
G = {'openpyxl': openpyxl, 're': re, 'datetime': datetime, 'html': html, 'get_column_letter': openpyxl.utils.get_column_letter}
G['esc'] = lambda s: html.escape(s, quote=True)
G['wb'] = openpyxl.Workbook()
exec(chunk, G)
wb = openpyxl.load_workbook(X); wv = openpyxl.load_workbook(X, data_only=True)
G['wb'] = wb; G['THEME'] = G['_theme_colors']()
vis = [ws for ws in wb if ws.sheet_state == 'visible']
parts = []
for ws in vis:
    body = G['render'](ws, wv[ws.title])
    parts.append((f'<h4 class="annex-doc-sheet">{html.escape(ws.title)}</h4>' if len(vis) > 1 else '') + body)
h = V2.read_text(encoding='utf-8')
m = re.search(r'<script id="jx-annex-docs">window\.ANNEX_DOCS = (\{.*?\});</script>', h, re.S)
docs = json.loads(m.group(1).replace('<\\/', '</'))
old = docs['6C']['content']
docs['6C']['content'] = ''.join(parts)
print('sheets', [w.title for w in vis], 'changed', old != docs['6C']['content'], len(old), len(docs['6C']['content']))
new_js = '<script id="jx-annex-docs">window.ANNEX_DOCS = ' + json.dumps(docs, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
h = h[:m.start()] + new_js + h[m.end():]
# text fixes
a = h.index('<section class="chap" id="ch3">'); b = h.index('<section class="chap" id="ch4">')
s3 = h[a:b]; n = len(re.findall(r'\bCV\b', s3))
s3 = re.sub(r'\bCV\b', 'resume', s3); h = h[:a] + s3 + h[b:]
a = h.index('<section class="chap" id="ch6">'); b = h.index('<section class="chap" id="ch7">')
s6 = h[a:b]; assert 'Benefit to the Dealer' in s6
s6 = s6.replace('Benefit to the Dealer', 'Benefit to Dealership'); h = h[:a] + s6 + h[b:]
print('CV->resume in ch3:', n)
V2.write_text(h, encoding='utf-8')
