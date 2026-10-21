"""Render JSW_HR_Manual_Annexures.xlsx into v2.html (rerunnable).

* every sheet -> window.ANNEX_DOCS[code] (HTML table, cell text verbatim)
* every chapter's "Annexure" list + the #annexure appendix -> "View File" items
  that open the existing #annexModal viewer
Chapter 6 (6A-6C) is "shared separately" in the workbook, so it is left alone.

usage: python3 portal-v7/annexures.py [xlsx]
"""
import base64, datetime, html, json, re, sys
from pathlib import Path
import openpyxl
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / 'v2.html'
XLSX = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Downloads/JSW_HR_Manual_Annexures.xlsx'

wb = openpyxl.load_workbook(XLSX)
wv = openpyxl.load_workbook(XLSX, data_only=True)
esc = lambda s: html.escape(s, quote=True)

# ---- index: code -> title (the workbook's own Index sheet) -------------------
TITLES = {}
for r in wb['Index'].iter_rows(min_row=5, values_only=True):
    if r[1] and r[2]:
        TITLES[str(r[1]).strip()] = str(r[2]).strip()

SHEET = {}
for ws in wb:
    m = re.match(r'^(\d+[A-Z])_', ws.title)
    if m:
        SHEET[m.group(1)] = ws.title


def fmt(v, nf):
    if v is None:
        return ''
    if isinstance(v, datetime.datetime):
        if 'h' in nf.lower() and 'd' not in nf.lower():
            return v.strftime('%H:%M')
        return v.strftime('%d-%b-%Y').lstrip('0')
    if isinstance(v, datetime.date):
        return v.strftime('%d-%b-%Y').lstrip('0')
    if isinstance(v, bool):
        return 'TRUE' if v else 'FALSE'
    if isinstance(v, (int, float)):
        if '%' in nf:
            d = len(nf.split('.')[1].rstrip('%')) if '.' in nf else 0
            return f'{v * 100:.{d}f}%'
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        if isinstance(v, float):
            d = len(nf.split('.')[1]) if '.' in nf and nf.split('.')[1].replace('0', '') == '' else None
            s = f'{v:,.{d}f}' if d is not None else f'{v:g}'
            return s
        return f'{v:,}' if ',' in nf else str(v)
    return str(v)


def rgb(c):
    try:
        if c is not None and c.type == 'rgb' and isinstance(c.rgb, str) and len(c.rgb) == 8 and c.rgb[:2] != '00':
            return '#' + c.rgb[2:]
    except Exception:
        pass
    return None


def border_css(c):
    b = c.border
    out = []
    for side, n in (('top', b.top), ('right', b.right), ('bottom', b.bottom), ('left', b.left)):
        out.append(f'border-{side}:1px solid #cbd5e1' if (n and n.style) else f'border-{side}:1px solid transparent')
    return ';'.join(out)


def render(ws, wsv, img_data=None):
    mr = {}
    skip = set()
    for rg in ws.merged_cells.ranges:
        mr[(rg.min_row, rg.min_col)] = (rg.max_row - rg.min_row + 1, rg.max_col - rg.min_col + 1)
        for r in range(rg.min_row, rg.max_row + 1):
            for c in range(rg.min_col, rg.max_col + 1):
                if (r, c) != (rg.min_row, rg.min_col):
                    skip.add((r, c))
    hidden_cols = {i for k, d in ws.column_dimensions.items() if d.hidden
                   for i in range(d.min or openpyxl.utils.column_index_from_string(k), (d.max or openpyxl.utils.column_index_from_string(k)) + 1)}
    maxr, maxc = ws.max_row, ws.max_column
    # trim trailing empty rows/cols
    def used(r, c):
        return wsv.cell(r, c).value not in (None, '') or ws.cell(r, c).border.top.style or ws.cell(r, c).border.bottom.style
    while maxr > 1 and not any(used(maxr, c) for c in range(1, maxc + 1)):
        maxr -= 1
    while maxc > 1 and not any(used(r, maxc) for r in range(1, maxr + 1)):
        maxc -= 1

    use = ''
    first = 1
    v1 = wsv.cell(1, 1).value
    if isinstance(v1, str) and v1.lstrip().lower().startswith('use:'):
        use = v1.strip()
        first = 2
        # drop the row's merged range so it is not rendered twice
    cols = [c for c in range(1, maxc + 1) if c not in hidden_cols]
    widths = []
    for c in cols:
        d = ws.column_dimensions.get(get_column_letter(c))
        w = d.width if d and d.width else 9
        widths.append(max(w, 4))
    tw = sum(widths) or 1
    out = [f'<div class="annex-doc-scroll"><table class="annex-xl" style="min-width:{max(640, int(tw * 7.5))}px"><colgroup>']
    out += [f'<col style="width:{w / tw * 100:.2f}%">' for w in widths]
    out.append('</colgroup><tbody>')
    for r in range(first, maxr + 1):
        cells = []
        for c in cols:
            if (r, c) in skip:
                continue
            cell = ws.cell(r, c)
            val = wsv.cell(r, c).value
            if val is None and not isinstance(cell.value, str):
                val = None
            txt = fmt(val, cell.number_format or '')
            rs, cs = mr.get((r, c), (1, 1))
            if rs > 1 and r + rs - 1 > maxr:
                rs = maxr - r + 1
            if cs > 1:
                cs = len([k for k in range(c, c + cs) if k in cols])
            st = [border_css(cell)]
            f = cell.font
            if f and f.b:
                st.append('font-weight:700')
            if f and f.i:
                st.append('font-style:italic')
            if f and f.u:
                st.append('text-decoration:underline')
            col = rgb(f.color) if f else None
            if col and col.lower() not in ('#000000',):
                st.append(f'color:{col}')
            fill = cell.fill
            if fill and fill.fill_type == 'solid':
                bg = rgb(fill.fgColor)
                if bg and bg.lower() != '#ffffff':
                    st.append(f'background:{bg}')
            a = cell.alignment
            if a and a.horizontal in ('center', 'right'):
                st.append(f'text-align:{a.horizontal}')
            if a and a.vertical in ('center', 'bottom'):
                st.append('vertical-align:' + ('middle' if a.vertical == 'center' else 'bottom'))
            body = esc(txt).replace('\n', '<br>')
            attrs = (f' rowspan="{rs}"' if rs > 1 else '') + (f' colspan="{cs}"' if cs > 1 else '')
            cells.append(f'<td{attrs} style="{";".join(st)}">{body}</td>')
        h = ws.row_dimensions[r].height if r in ws.row_dimensions else None
        out.append(f'<tr{f" style=\"height:{h * 1.25:.0f}px\"" if h else ""}>{"".join(cells)}</tr>')
    out.append('</tbody></table></div>')
    pre = f'<p class="annex-doc-use">{esc(use)}</p>' if use else ''
    img = f'<img class="annex-doc-img" alt="" src="{img_data}">' if img_data else ''
    return pre + ''.join(out) + img


# 3D is a picture
img3d = None
for ws in wb:
    if ws.title.startswith('3D') and ws._images:
        img3d = 'data:image/jpeg;base64,' + base64.b64encode(ws._images[0]._data()).decode()

docs = {}
for code, sname in SHEET.items():
    ws, wsv = wb[sname], wv[sname]
    body = render(ws, wsv, img3d if code == '3D' else None)
    docs[code] = {
        'code': code, 'title': TITLES.get(code, ''),
        'filename': f'{code}_{re.sub(r"[^A-Za-z0-9]+", "_", TITLES.get(code, "")).strip("_")}.doc',
        'content': body,
    }

CSS = """<style id="jx-annex-docs-css">
.annex-modal-dialog{max-width:1180px !important}
.annex-doc-use{margin:0 0 14px;padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;color:#475569}
.annex-doc-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table.annex-xl{border-collapse:collapse;table-layout:fixed;width:100%;min-width:640px;font-size:12.5px;line-height:1.45;color:#1e293b}
table.annex-xl td{padding:5px 8px;vertical-align:top;overflow-wrap:anywhere;word-break:normal}
.annex-doc-img{display:block;max-width:100%;height:auto;margin-top:14px;border:1px solid #e2e8f0}
</style>"""

JS = ('<script id="jx-annex-docs">window.ANNEX_DOCS = '
      + json.dumps(docs, ensure_ascii=False).replace('</', '<\\/') + ';</script>')

EYE = ('<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">'
       '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>')


def item(code, with_id):
    t = f'{code}. {TITLES[code]}'
    return (f'<div{f" id=\"annex-{code}\"" if with_id else ""} class="annex-file-item" role="button" tabindex="0" '
            f'title="View {esc(t)}" onclick="openAnnexViewer(event, \'{code}\')" '
            f'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){{openAnnexViewer(event, \'{code}\')}}">'
            f'<div class="annex-file-left"><div class="annex-file-icon">📄</div>'
            f'<div class="annex-file-name">{esc(t)}</div></div>'
            f'<div class="annex-view-badge">{EYE} View File</div></div>')


def chap_codes(n):
    return [c for c in TITLES if re.match(rf'^{n}[A-Z]$', c)]


h = V2.read_text()
orig_len = len(h)

# drop earlier injection
h = re.sub(r'<style id="jx-annex-docs-css">.*?</style>\n?', '', h, flags=re.S)
h = re.sub(r'<script id="jx-annex-docs">.*?</script>\n?', '', h, flags=re.S)

# 1) per-chapter lists (chapters 3-5, 7-12; ch6 untouched; ch2 JD list already uses the viewer)
sec_start = {int(m.group(1)): m.start() for m in re.finditer(r'<section class="chap" id="ch(\d+)">', h)}
order = sorted(sec_start.items(), key=lambda kv: kv[1])
LIST_RE = re.compile(r'(<p><strong style="color:var\(--ink\)">Annexure</strong></p>\n)(?:<!--annex-list-->.*?<!--/annex-list-->\n?|(?:<a class="annex-file-item"[^\n]*</a>\n?)+)', re.S)
wrap = lambda items: '<!--annex-list-->' + '<div class="annex-file-list">' + items + '</div>' + '<!--/annex-list-->\n'
done = []
for i in range(len(order) - 1, -1, -1):
    n, st = order[i]
    en = order[i + 1][1] if i + 1 < len(order) else len(h)
    if n in (1, 2, 6):
        continue
    seg = h[st:en]
    codes = chap_codes(n)
    if not codes:
        continue
    new, k = LIST_RE.subn(lambda m: m.group(1) + wrap(''.join(item(c, False) for c in codes)), seg, count=1)
    if k:
        h = h[:st] + new + h[en:]
        done.append(n)

# 2) the appendix (#annexure): same items, keep anchor ids used by the in-text chips
a0 = h.index('<section class="chap" id="annexure">')
a1 = h.index('</section>', a0)
app = h[a0:a1]
for n in range(2, 13):
    if n == 6:
        continue
    pat = re.compile(rf'(?:<!--annex-list-->.*?<!--/annex-list-->\n?|(?:<a id="annex-{n}[A-Z]"[^\n]*</a>\n?)+)', re.S)
    # appendix: a list per chapter heading, so only look after that chapter's <h3>
    hs = app.index(f'id="annex-{n}"')
    tail = pat.sub(lambda m: wrap(''.join(item(c, True) for c in chap_codes(n))), app[hs:], count=1)
    app = app[:hs] + tail
h = h[:a0] + app + h[a1:]

# 3) docs + css just before the viewer script
anchor = '<!-- ============ ANNEXURE DOCUMENT VIEWER MODAL ============ -->'
assert anchor in h
h = h.replace(anchor, CSS + '\n' + JS + '\n' + anchor, 1)

# 4) download = the rendered document as a Word-openable .doc (was a flattened text dump)
DL_NEW = """var htmlDoc = '<html><head><meta charset="utf-8"><title>' + doc.code + ' ' + doc.title + '</title><style>table{border-collapse:collapse}td{padding:4px 6px;font:11pt Calibri,Arial,sans-serif;vertical-align:top}</style></head><body>' + doc.content + '</body></html>';
        var blob = new Blob(['\\ufeff', htmlDoc], { type: 'application/msword;charset=utf-8' });"""
h2 = re.sub(r"var textContent = doc\.title.*?var blob = new Blob\(\[textContent\], \{ type: 'application/msword;charset=utf-8' \}\);",
            lambda m: DL_NEW, h, count=1, flags=re.S)
h = h2

V2.write_text(h)
print('chapters rewired:', sorted(done), '| docs:', len(docs), '| size delta', len(h) - orig_len)
