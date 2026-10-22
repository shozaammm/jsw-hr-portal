"""Annexure feedback round (2026-10-22), applied to v2.html. Rerunnable.

1. Annexures page: each row shows the workbook's Index "Use / Used by" line (text verbatim from the Index sheet)
2. plain-text annexure references in ch3/ch4/ch7 become links (they open the annexure light-box)
3. annexure rows no longer slide 5px right on hover (that overflow made a horizontal scrollbar appear)

usage: python3 portal-v7/annex_index.py [Annexures.xlsx]
"""
import html, re, sys, warnings
from pathlib import Path
import openpyxl

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / 'v2.html'
XLSX = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Downloads/JSW_HR_Manual_Annexures.xlsx'

DESC = {}
for r in openpyxl.load_workbook(XLSX, data_only=True)['Index'].iter_rows(min_row=5, values_only=True):
    if r[1] and r[3]:
        DESC[str(r[1]).strip()] = re.sub(r'\s+', ' ', str(r[3])).strip()
# 6A-6C come from the separately shared workbooks, whose Index rows live in the same sheet
h = V2.read_text(encoding='utf-8')
esc = lambda s: html.escape(s, quote=False)


def desc_html(text):
    parts = [p.strip() for p in text.split('|')]
    out = []
    for p in parts:
        k, _, v = p.partition(':')
        out.append(f'<span><b>{esc(k)}:</b> {esc(v.strip())}</span>')
    return '<div class="annex-file-desc">' + ''.join(out) + '</div>'


# ---------- 1. descriptions on the Annexures page ----------
a0 = h.index('<section class="chap" id="annexure">')
a1 = h.index('<!-- ============ ANNEXURE DOCUMENT VIEWER MODAL')
app = h[a0:a1]
ROW = re.compile(r'(<div id="annex-(\w+)" class="annex-file-item"[^>]*>)<div class="annex-file-left"><div class="annex-file-icon">📄</div>'
                 r'<div class="annex-file-name">(.*?)</div></div>')
missing = []


def row(m):
    code = m.group(2)
    if code not in DESC:
        missing.append(code)
        return m.group(0)
    return (m.group(1) + '<div class="annex-file-left"><div class="annex-file-icon">📄</div><div class="annex-file-text">'
            f'<div class="annex-file-name">{m.group(3)}</div>{desc_html(DESC[code])}</div></div>')


app = ROW.sub(row, app)
h = h[:a0] + app + h[a1:]

# ---------- 2. plain-text references -> links (outside <script>) ----------
L = lambda code, text=None, cls='v7-ref': f'<a class="{cls}" href="#annex-{code}">{text or code}</a>'
LT = lambda code, text: L(code, text, 'v7-ref v7-ref-title')
SWAPS = [
    ('<em>3B. Internal Job Posting (IJP) Template</em>', f'<em>{LT("3B", "3B. Internal Job Posting (IJP) Template")}</em>'),
    ('<em>3C. Internal Job Posting Application Form</em>', f'<em>{LT("3C", "3C. Internal Job Posting Application Form")}</em>'),
    ('<em>3D. Recruitment ad template</em>', f'<em>{LT("3D", "3D. Recruitment ad template")}</em>'),
    ('<em>3E. Employee referral form</em>', f'<em>{LT("3E", "3E. Employee referral form")}</em>'),
    ('<em>3H. Reference check form and 3I. Background verification form</em>',
     f'<em>{LT("3H", "3H. Reference check form")} and {LT("3I", "3I. Background verification form")}</em>'),
    ('<em>*Please refer 4A for a sample salary slip</em>', f'<em>*Please refer {L("4A")} for a sample salary slip</em>'),
    ('<em>*Please refer to 4C. Advance Salary Request Form</em>', f'<em>*Please refer to {LT("4C", "4C. Advance Salary Request Form")}</em>'),
    ('check KPIs progress using annexure 7B</h5>', f'check KPIs progress using annexure {L("7B")}</h5>'),
    ('against each KPI in annexure 7B and calculate the rating and grade</h5>', f'against each KPI in annexure {L("7B")} and calculate the rating and grade</h5>'),
]
chunks = re.split(r'(<script\b.*?</script>)', h, flags=re.S)
for old, new in SWAPS:
    n = sum(c.count(old) for c in chunks if not c.startswith('<script'))
    if n == 0:
        continue  # already applied
    assert n == 1, (old, n)
    chunks = [c if c.startswith('<script') else c.replace(old, new) for c in chunks]
h = ''.join(chunks)

# ---------- css ----------
if 'id="jx-annex-fix-css"' not in h:
    CSS = r'''<style id="jx-annex-fix-css">
/* a hovered row used to shift 5px right, which pushed the page wider than the screen and showed a horizontal scrollbar */
.annex-file-item:hover{transform:none !important}
.annex-file-text{min-width:0;display:flex;flex-direction:column;gap:5px}
.annex-file-desc{display:flex;flex-direction:column;gap:1px;font-size:12.5px;line-height:1.5;font-weight:400;color:#5f5f64}
.annex-file-desc b{font-weight:650;color:#3a3a3e}
.annex-file-item:has(.annex-file-desc) .annex-file-left{align-items:flex-start}
.annex-file-item:has(.annex-file-desc) .annex-file-icon{margin-top:2px}
.annex-file-item:has(.annex-file-desc){gap:14px}
.annex-file-item:has(.annex-file-desc) .annex-view-badge{flex:none}
@media(max-width:600px){.annex-file-item:has(.annex-file-desc){flex-direction:column !important;align-items:stretch !important;gap:10px !important}.annex-file-item:has(.annex-file-desc) .annex-view-badge{justify-content:center}}
/* a reference that names its annexure ("3D. Recruitment ad template") reads as a link, not a chip */
.jx-chapter a.v7-ref.v7-ref-title{display:inline;padding:0 1px;border:0;border-bottom:1.5px solid currentColor;border-radius:2px;background:none;font-size:inherit;font-weight:650;font-style:inherit;letter-spacing:0;white-space:normal;vertical-align:baseline}
.jx-chapter a.v7-ref.v7-ref-title:hover{background:#1B1B1D;color:#fff;border-bottom-color:#1B1B1D}
</style>
'''
    h = h.replace('<style id="jx-annex-docs-css">', CSS + '<style id="jx-annex-docs-css">', 1)

V2.write_text(h, encoding='utf-8')
print('ok; rows without an Index entry:', missing)
