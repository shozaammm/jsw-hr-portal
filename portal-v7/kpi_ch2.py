"""Chapter 2 KPIs replaced from Dealership_KPI_Framework_Reviewed.xlsx. Rerunnable, applied to v2.html.

Touches the KPI section of each mapped role in (a) the chapter 2 role pages (#rd-role-N) and (b) annexure 2B
(All Job Descriptions). Annexure 7A (KPIs Laundry List, chapter 7) is not touched.
KPI text is the workbook's own; a '>' note after the arrow is shown as a muted second line.

usage: python3 portal-v7/kpi_ch2.py [xlsx]
"""
import html, json, re, sys, warnings
from pathlib import Path
import openpyxl

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / 'v2.html'
XL = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Downloads/Dealership_KPI_Framework_Reviewed.xlsx'
esc = lambda s: html.escape(s, quote=False)

# workbook column header -> portal role id (#rd-role-N)
MAP = {'Sales Consultant': 10, 'Team Leader': 11, 'Sales Manager': 6, 'GM (Sales)': 1, 'CEO/Business Head': 0,
       'Marketing Manager': 7, 'Marketing Executive': 26, 'Showroom Hostess': 21, 'Sales Training Manager': 9,
       'CRM Manager': 5}

norm = lambda s: re.sub(r'\s+', ' ', str(s).replace('\xa0', ' ')).strip()

# ---------------------------------------------------------------- workbook
ws = openpyxl.load_workbook(XL).active
rows = [r for r in ws.iter_rows(values_only=True)]
kpis = {}
cols = None
for r in rows:
    if r[0] == 'KPI/Role':
        cols = {i: norm(v) for i, v in enumerate(r) if i and v}
        continue
    if cols is None:
        continue
    for i, role in cols.items():
        v = r[i] if i < len(r) else None
        if v is None or not norm(v):
            continue
        name, _, note = norm(v).partition('►')
        kpis.setdefault(role, []).append((name.strip(), note.strip()))
missing = [k for k in MAP if k not in kpis]
assert not missing, missing

h = V2.read_text(encoding='utf-8')

# ---------------------------------------------------------------- role pages
def role_html(items):
    li = ''.join(f'<li>{esc(n)}' + (f'<span class="rd-kpi-note">{esc(t)}</span>' if t else '') + '</li>'
                 for n, t in items)
    return f'<div class="rd-kpi-group"><ul class="list-clean">{li}</ul></div>'

K = '<h4 class="rd-sub">4. Key Performance Indicators (KPIs)</h4>'
C = '<h4 class="rd-sub">5. Key Competencies</h4>'
for role, rid in MAP.items():
    a = h.index(f'<div id="rd-role-{rid}">')
    k = h.index(K, a) + len(K)
    c = h.index(C, k)
    assert c - a < 60000, (role, 'KPI section not inside role block')
    h = h[:k] + role_html(kpis[role]) + h[c:]

# ---------------------------------------------------------------- annexure 2B
m = re.search(r'<script id="jx-annex-docs">window\.ANNEX_DOCS = (\{.*?\});</script>', h, re.S)
docs = json.loads(m.group(1))
c2 = docs['2B']['content']
rowre = re.compile(r'<tr>.*?</tr>', re.S)
trs = list(rowre.finditer(c2))
txt = lambda t: html.unescape(re.sub(r'<[^>]+>', '', t)).strip()
kidx = [i for i, t in enumerate(trs) if txt(t.group()).startswith('4. Key Performance Indicators')]
assert len(kidx) == 34, len(kidx)
tmpl = next(t.group() for t in trs[kidx[0] + 2:kidx[0] + 3])  # a plain KPI row (colspan=2) to copy styles from
cell = lambda s: re.sub(r'(<td[^>]*>).*?(</td>)', lambda x: x.group(1) + esc(s) + x.group(2), tmpl, count=1, flags=re.S)
role_of = {}
for n, ki in enumerate(kidx):
    j = ki
    while not txt(trs[j].group()).startswith('Department'):
        j -= 1
    role_of[n] = txt(trs[j - 1].group())
# portal role titles (same order as the role pages) to confirm 2B blocks line up with the role ids
page_titles = [html.unescape(t) for t in re.findall(r'class="rd-detail-title">(.*?)<', h)]
for rid in MAP.values():
    assert role_of[rid] == page_titles[rid], (rid, role_of[rid], page_titles[rid])
out, pos = [], 0
for rid in sorted(MAP.values()):
    role = next(r for r, i in MAP.items() if i == rid)
    ks, ke = kidx[rid], kidx[rid] + 1
    kc = ke
    while not txt(trs[kc].group()).startswith('5. Key Competencies'):
        kc += 1
    new = ''.join(cell(n + (f' ► {t}' if t else '')) for n, t in kpis[role])
    out.append(c2[pos:trs[ke].start()])
    out.append(new)
    pos = trs[kc].start()
out.append(c2[pos:])
docs['2B']['content'] = ''.join(out)
new_js = '<script id="jx-annex-docs">window.ANNEX_DOCS = ' + json.dumps(docs, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
h = h[:m.start()] + new_js + h[m.end():]

# ---------------------------------------------------------------- css
CSS = ('<style id="jx-kpi-css">.rd-kpi-note{display:block;font-size:12px;font-weight:400;color:var(--grey-500);'
       'margin-top:2px;line-height:1.4}</style>')
if 'id="jx-kpi-css"' in h:
    h = re.sub(r'<style id="jx-kpi-css">.*?</style>', lambda _: CSS, h, count=1, flags=re.S)
else:
    h = h.replace('<style id="jx-annex-docs-css">', CSS + '<style id="jx-annex-docs-css">', 1)

V2.write_text(h, encoding='utf-8')
print('updated roles:', ', '.join(f'{r}({len(kpis[r])})' for r in MAP))
