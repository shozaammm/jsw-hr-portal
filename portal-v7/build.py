#!/usr/bin/env python3
"""Rebuild v2.html content from the HR Manual V7 Word file.

Base   : v2.html at BASE_COMMIT (rerunnable; never reads the working copy).
Source : HR Manual V7 01.10.26.docx — the only source of manual text.
Kept   : shell, styles, home, Ch.1 org-chart component, Ch.2 Job Descriptions.
Rebuilt: intro pages i-iii, chapters 3-12, annexure, JX_TOC.

Text is copied verbatim from the docx. Layout reuses the portal's own
classes (pull, meta-row, sub-title, item-title, list-clean, table-wrap,
zigzag, img-card, annex-file-item).
"""
import base64, hashlib, html, io, json, re, subprocess, sys
from pathlib import Path

import docx
import flowcharts as fc
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

REPO = Path(__file__).resolve().parent.parent
BASE_COMMIT = '9abbb59'
DOCX = Path.home() / 'Downloads' / 'HR Manual V7 01.10.26.docx'
OUT = REPO / 'v2.html'

HEAD_BLUE = '0F4761'
MINOR_GREY = '595959'
RMS_FILL = 'FAE2D5'        # "Orange box steps are to be done on the RMS tool"
ARROWS = set('→←↓↑')

esc = lambda s: html.escape(s, quote=False)


# ───────────────────────────── docx model ─────────────────────────────
class Doc:
    def __init__(self, path):
        self.d = docx.Document(str(path))
        num = self.d.part.numbering_part.element
        self.absmap = {n.get(qn('w:numId')): n.find(qn('w:abstractNumId')).get(qn('w:val'))
                       for n in num.findall(qn('w:num'))}
        self.lvls = {}
        for a in num.findall(qn('w:abstractNum')):
            for l in a.findall(qn('w:lvl')):
                f, t, s = l.find(qn('w:numFmt')), l.find(qn('w:lvlText')), l.find(qn('w:start'))
                self.lvls[(a.get(qn('w:abstractNumId')), int(l.get(qn('w:ilvl'))))] = (
                    f.get(qn('w:val')) if f is not None else 'bullet',
                    t.get(qn('w:val')) if t is not None else '',
                    int(s.get(qn('w:val'))) if s is not None else 1)
        self.counters = {}
        self.blocks = [b for b in (self.block(el) for el in self.d.element.body.iterchildren()) if b]

    # numbering ---------------------------------------------------------
    def numinfo(self, p):
        ppr = p._p.pPr
        if ppr is None or ppr.numPr is None or ppr.numPr.numId is None:
            return None
        nid = str(ppr.numPr.numId.val)
        if nid == '0':
            return None
        il = ppr.numPr.ilvl.val if ppr.numPr.ilvl is not None else 0
        aid = self.absmap.get(nid)
        fmt, txt, start = self.lvls.get((aid, il), ('bullet', '', 1))
        marker = ''
        if fmt not in ('bullet', 'none'):
            c = self.counters.setdefault(aid, {})
            c[il] = c.get(il, start - 1) + 1
            for k in [k for k in c if k > il]:
                del c[k]
            def lvl_val(m):
                k = int(m.group(1)) - 1
                f2 = self.lvls.get((aid, k), ('decimal', '', 1))[0]
                v = c.get(k, self.lvls.get((aid, k), ('', '', 1))[2])
                if f2 == 'lowerLetter': return chr(96 + v)
                if f2 == 'upperLetter': return chr(64 + v)
                if f2 == 'lowerRoman': return roman(v).lower()
                if f2 == 'upperRoman': return roman(v)
                return str(v)
            marker = re.sub(r'%(\d)', lvl_val, txt)
        return {'ilvl': il, 'fmt': fmt, 'marker': marker}

    # inline runs -----------------------------------------------------
    def runs_html(self, p):
        out = []
        for r in p.runs:
            t = r.text
            if not t:
                continue
            h = esc(t)
            if r.bold and t.strip():
                h = f'<strong>{h}</strong>'
            if r.italic and t.strip():
                h = f'<em>{h}</em>'
            out.append(h)
        s = ''.join(out)
        s = re.sub(r'</strong>(\s*)<strong>', r'\1', s)
        s = re.sub(r'</em>(\s*)<em>', r'\1', s)
        return s.strip()

    def images(self, el):
        """(mime, bytes, display width px) — Word's own crop (srcRect) applied, display size from wp:extent."""
        from PIL import Image
        out = []
        for dr in el.iter(qn('w:drawing')):
            blip = dr.find('.//' + qn('a:blip'))
            if blip is None:
                continue
            part = self.d.part.related_parts[blip.get(qn('r:embed'))]
            blob, mime = part.blob, part.content_type
            src = dr.find('.//' + qn('a:srcRect'))
            if src is not None and any(int(src.get(k, 0)) > 0 for k in 'lrtb'):
                im = Image.open(io.BytesIO(blob)); w, h = im.size
                f = lambda k: max(0, int(src.get(k, 0))) / 100000
                im = im.crop((round(w * f('l')), round(h * f('t')), round(w * (1 - f('r'))), round(h * (1 - f('b')))))
                buf = io.BytesIO(); im.save(buf, 'PNG'); blob, mime = buf.getvalue(), 'image/png'
            ext = dr.find('.//' + qn('wp:extent'))
            width = round(int(ext.get('cx')) / 9525) if ext is not None else None
            out.append((mime, blob, width, hashlib.md5(part.blob).hexdigest()[:8]))
        return out

    def fmt(self, p):
        sizes, colors, bold = set(), set(), []
        for r in p.runs:
            if not r.text.strip():
                continue
            sizes.add(r.font.size.pt if r.font.size else None)
            colors.add(str(r.font.color.rgb) if r.font.color is not None and r.font.color.type is not None else None)
            bold.append(bool(r.bold))
        return sizes, colors, (bool(bold) and all(bold))

    def block(self, el):
        tag = el.tag.split('}')[1]
        if tag == 'tbl':
            return {'k': 'tbl', 't': Table(el, self.d)}
        if tag != 'p':
            return None
        p = Paragraph(el, self.d)
        text = p.text
        imgs = self.images(el)
        if not text.strip() and not imgs:
            return None
        style = p.style.name if p.style is not None else 'Normal'
        num = self.numinfo(p)
        sizes, colors, allbold = self.fmt(p)
        lvl = 0
        m = re.match(r'Heading (\d)', style)
        if m:
            lvl = int(m.group(1))
        elif HEAD_BLUE in colors and not num:
            sz = max([s for s in sizes if s] or [0])
            lvl = 2 if sz >= 15.5 else 3 if sz >= 13.5 else 4
        elif MINOR_GREY in colors and not num and len(text) < 120:
            lvl = 5
        return {'k': 'p', 'p': p, 'style': style, 'text': text.strip(), 'html': self.runs_html(p),
                'num': num, 'lvl': lvl, 'imgs': imgs, 'bold': allbold}


def roman(n):
    vals = [(10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    s = ''
    for v, r in vals:
        while n >= v:
            s += r; n -= v
    return s


# ───────────────────────────── tables ─────────────────────────────
def cells_of(row):
    seen, out = set(), []
    for c in row.cells:
        if id(c._tc) in seen:
            continue
        seen.add(id(c._tc))
        out.append(c)
    return out


def cell_fill(c):
    shd = c._tc.find('.//' + qn('w:shd'))
    return (shd.get(qn('w:fill')) or '').upper() if shd is not None else ''


def is_flow(t):
    return any(c.text.strip() in ARROWS for r in t.rows for c in r.cells)


def flow_steps(t):
    """Steps in reading order: rows containing ← read right-to-left."""
    steps = []
    for r in t.rows:
        cells = [c for c in cells_of(r) if c.text.strip() and c.text.strip() not in ARROWS]
        if any(c.text.strip() == '←' or c.text.strip().endswith('←') for c in cells_of(r)):
            cells = cells[::-1]
        steps.extend(cells)
    return steps


def parse_step(c, idx):
    """(num, when[], body[], who[], rms) for one flow-table cell."""
    paras = [p for p in c.paragraphs if p.text.strip() and p.text.strip() not in ARROWS]
    li = next((i for i, p in enumerate(paras) if re.match(r'^[A-Z]\.\s', p.text.strip())), None)
    num, when, body, who = f'{idx:02d}', [], [], []
    if li is None:
        body = [paras[0].text.strip()] if paras else []
        rest = paras[1:]
    else:
        when = [p.text.strip() for p in paras[:li]]
        m = re.match(r'^([A-Z])\.\s*(.*)$', paras[li].text.strip())
        num, body = m.group(1), [m.group(2)]
        rest = paras[li + 1:]
    for p in rest:
        rs = [r for r in p.runs if r.text.strip()]
        role = rs and all(r.italic or r.bold for r in rs)
        (who if role or who else body).append(p.text.strip())
    return num, when, body, who, cell_fill(c) == RMS_FILL


def flow_cells(tables):
    out, i = [], 1
    for t in tables:
        for c in flow_steps(t):
            out.append(parse_step(c, i)); i += 1
    return out


def step_html(c, idx):
    paras = [p for p in c.paragraphs if p.text.strip() and p.text.strip() not in ARROWS]
    li = next((i for i, p in enumerate(paras) if re.match(r'^[A-Z]\.\s', p.text.strip())), None)
    num, when, body, who = f'{idx:02d}', [], [], []
    if li is None:
        # no lettered line: first para is the step, italic/bold-only trailing paras are roles
        body = [paras[0].text.strip()] if paras else []
        rest = paras[1:]
    else:
        when = [p.text.strip() for p in paras[:li]]
        m = re.match(r'^([A-Z])\.\s*(.*)$', paras[li].text.strip())
        num, body = m.group(1), [m.group(2)]
        rest = paras[li + 1:]
    for p in rest:
        rs = [r for r in p.runs if r.text.strip()]
        role = rs and all(r.italic or r.bold for r in rs)
        (who if role or who else body).append(p.text.strip())
    inner = ''
    if when:
        inner += f'<span class="zz-when">{esc(" ".join(when))}</span>'
    inner += f'<span class="zz-text">{esc(" ".join(body))}</span>'
    for w in who:
        inner += f'<span class="zz-who">{esc(w)}</span>'
    out = f'<span class="zz-num">{esc(num)}</span><span class="zz-body">{inner}</span>'
    cls = 'zigzag-pill zz-rms' if cell_fill(c) == RMS_FILL else 'zigzag-pill'
    return f'<div class="zigzag-item"><div class="{cls}">{out}</div></div>'


def flow_nodes(tables):
    """Steps with their grid position, exactly as the Word tables lay them out (arrow cells sit between step cells)."""
    nodes, row0, idx = [], 0, 1
    for t in tables:
        used = 0
        for r in t.rows:
            cells, col = [], 0
            for c in cells_of(r):
                span = c._tc.tcPr.gridSpan.val if c._tc.tcPr is not None and c._tc.tcPr.gridSpan is not None else 1
                cells.append((col, c)); col += span
            steps = [(k, c) for k, c in cells if c.text.strip() and c.text.strip() not in ARROWS]
            if not steps:
                continue
            used += 1
            if any(c.text.strip() == '←' or c.text.strip().endswith('←') for _, c in cells):
                steps = steps[::-1]
            for k, c in steps:
                num, when, body, who, rms = parse_step(c, idx)
                nodes.append({'num': str(int(num)) if re.fullmatch(r'0\d', num) else num, 'when': when, 'body': body,
                              'who': who, 'rms': rms, 'row': row0 + used, 'col': k // 2 + 1})
                idx += 1
        row0 += used
    return nodes


def flow_html(tables):
    items, i = [], 1
    for t in tables:
        for c in flow_steps(t):
            items.append(step_html(c, i)); i += 1
    return '<div class="zigzag">' + ''.join(items) + '</div>'


def cell_html(c, D):
    """Cell paragraphs → bullets if several, plain text otherwise."""
    paras = [p for p in c.paragraphs if p.text.strip()]
    if not paras:
        return ''
    if len(paras) == 1:
        return D.runs_html(paras[0])
    listed = lambda p: p._p.pPr is not None and p._p.pPr.numPr is not None
    if all(listed(p) for p in paras):
        return '<ul class="cell-bullets">' + ''.join(f'<li>{D.runs_html(p)}</li>' for p in paras) + '</ul>'
    out, buf = [], []
    for p in paras:          # plain lines keep their line breaks; real list runs become bullets
        if listed(p):
            buf.append(f'<li>{D.runs_html(p)}</li>')
            continue
        if buf:
            out.append('<ul class="cell-bullets">' + ''.join(buf) + '</ul>'); buf = []
        out.append(D.runs_html(p) + '<br>')
    if buf:
        out.append('<ul class="cell-bullets">' + ''.join(buf) + '</ul>')
    return re.sub(r'<br>$', '', ''.join(out))


def sections_html(rows, D):
    """One-column box whose rows are 'title + bullets' (e.g. How to make an IJP): each row is its own titled section."""
    out = []
    for r in rows:
        paras = [p for p in r[0].paragraphs if p.text.strip()]
        listed = lambda p: p._p.pPr is not None and p._p.pPr.numPr is not None
        body, buf = [], []
        for p in paras[1:]:
            if listed(p):
                buf.append(f'<li>{D.runs_html(p)}</li>')
                continue
            if buf:
                body.append('<ul class="cell-bullets">' + ''.join(buf) + '</ul>'); buf = []
            body.append(f'<p class="v7-sec-note">{D.runs_html(p)}</p>')
        if buf:
            body.append('<ul class="cell-bullets">' + ''.join(buf) + '</ul>')
        out.append(f'<section class="v7-sec"><h4 class="v7-sec-title">{D.runs_html(paras[0])}</h4>{"".join(body)}</section>')
    return '<div class="v7-panel">' + ''.join(out) + '</div>'


def table_html(t, D):
    rows = [cells_of(r) for r in t.rows]
    rows = [r for r in rows if any(c.text.strip() for c in r)]
    if not rows:
        return ''
    ncol = max(len(r) for r in rows)
    if ncol == 1 and any(len([p for p in r[0].paragraphs if p.text.strip()]) > 1 for r in rows):
        return sections_html(rows, D)
    head, body = rows[0], rows[1:]
    # a first row that is one merged banner (e.g. "SECTION 1 — …") stays a full-width header
    def tr(cells, tag):
        out = []
        for c in cells:
            span = c._tc.tcPr.gridSpan.val if c._tc.tcPr is not None and c._tc.tcPr.gridSpan is not None else 1
            a = f' colspan="{span}"' if span > 1 else ''
            out.append(f'<{tag}{a}>{cell_html(c, D)}</{tag}>')
        return '<tr>' + ''.join(out) + '</tr>'
    if ncol == 1:   # single-column boxes (e.g. "How to make an IJP") read as a titled list
        return ('<div class="table-wrap"><table><thead>' + tr(head, 'th') + '</thead><tbody>'
                + ''.join(tr(r, 'td') for r in body) + '</tbody></table></div>')
    return ('<div class="table-wrap"><table><thead>' + tr(head, 'th') + '</thead><tbody>'
            + ''.join(tr(r, 'td') for r in body) + '</tbody></table></div>')


# ───────────────────────────── renderer ─────────────────────────────
META = re.compile(r'^(Purpose|Principles|Benefits? to (?:the )?(?:Dealers?|Dealerships?|Customers?))\s*:?\s*$', re.I)
ANNEX = re.compile(r'^ANNEXT?URES?$')
ANNEX_ITEM = re.compile(r'^(\d{1,2}[A-Z])\.\s+(.+)$')
DOWNLOAD_SVG = ('<svg fill="none" height="12" stroke="currentColor" stroke-width="2.5" viewbox="0 0 24 24" width="12">'
                '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline>'
                '<line x1="12" x2="12" y1="15" y2="3"></line></svg>')


def img_html(imgs, alt):
    out = []
    for mime, blob, width, _ in imgs:
        b64 = base64.b64encode(blob).decode()
        mw = f' style="max-width:{width}px"' if width else ''
        out.append(f'<div class="img-card v7-img"{mw}><img alt="{html.escape(alt)}" loading="lazy" src="data:{mime};base64,{b64}"/></div>')
    return ''.join(out)


def annex_html(code, name):
    title = f'{code}. {name}'
    t = html.escape(title, quote=True).replace("'", "\\'")
    return (f'<a class="annex-file-item" href="#annexure" onclick="handleAnnexDownload(event, \'{t}\')" title="Download {html.escape(title)}">'
            f'<div class="annex-file-left"><div class="annex-file-icon">📄</div><div class="annex-file-name">{esc(title)}</div></div>'
            f'<div class="annex-dl-badge">{DOWNLOAD_SVG} Download File</div></a>')


class Renderer:
    def __init__(self, D, chap_id):
        self.D, self.cid = D, chap_id
        self.out, self.subs = [], []
        self.list_stack = []        # open <ul> levels
        self.meta_open = False
        self.seen_h2 = False
        self.pull_done = False
        self.annex = []             # (code, name) collected for the consolidated page
        self.in_annex = False

    def close_lists(self, to=-1):
        while len(self.list_stack) > to + 1:
            self.out.append('</li></ul>')
            self.list_stack.pop()

    def close_meta(self):
        self.close_lists()
        if self.meta_open:
            self.out.append('</div></div>')
            self.meta_open = False

    def li(self, b):
        lvl = b['num']['ilvl'] if b['num'] else 0
        marker = b['num']['marker'] if b['num'] else ''
        body = (esc(marker) + ' ' if marker else '') + b['html']
        if not self.list_stack:
            self.out.append('<ul class="list-clean">' if not self.meta_open else '<ul class="list-clean" style="margin-top:4px;">')
            self.list_stack.append(lvl)
            self.out.append('<li>' + body)
            return
        if lvl > self.list_stack[-1]:
            self.out.append('<ul class="list-clean">')
            self.list_stack.append(lvl)
            self.out.append('<li>' + body)
            return
        while len(self.list_stack) > 1 and lvl < self.list_stack[-1]:
            self.out.append('</li></ul>')
            self.list_stack.pop()
        self.out.append('</li><li>' + body)

    hooks = None      # set by build(): fn(renderer, blocks, i) -> (html, consumed) | None

    def render(self, blocks):
        i = 0
        while i < len(blocks):
            b = blocks[i]
            hit = Renderer.hooks(self, blocks, i) if Renderer.hooks else None
            if hit:
                self.close_meta()
                self.out.append(hit[0])
                i += hit[1]; continue
            if b['k'] == 'tbl':
                self.close_meta()
                if is_flow(b['t']):
                    group = [b['t']]
                    while True:
                        j = i + 1       # a lone ↓ paragraph between two flow tables continues the same flow
                        if j < len(blocks) and blocks[j]['k'] == 'p' and blocks[j]['text'] in ARROWS and not blocks[j]['imgs']:
                            j += 1
                        if j < len(blocks) and blocks[j]['k'] == 'tbl' and is_flow(blocks[j]['t']):
                            group.append(blocks[j]['t']); i = j
                            continue
                        break
                    self.out.append(fc.snake(flow_nodes(group)))
                else:
                    self.out.append(table_html(b['t'], self.D))
                i += 1; continue
            self.para(b)
            i += 1
        self.close_meta()
        return '\n'.join(self.out)

    def para(self, b):
        t, h = b['text'], b['html']
        # annexure list at chapter end
        if ANNEX.match(t):
            self.close_meta()
            self.in_annex = True
            self.out.append(f'<p><strong style="color:var(--ink)">{esc(t)}</strong></p>')
            return
        if self.in_annex:
            m = ANNEX_ITEM.match(t)
            if m:
                self.annex.append((m.group(1), m.group(2)))
                self.out.append(annex_html(m.group(1), m.group(2)))
                return
            self.in_annex = False
        if b['imgs']:
            self.close_meta()
            self.out.append(img_html(b['imgs'], t or 'Illustration'))
            if t:
                self.out.append(f'<p>{h}</p>')
            return
        opener = (not self.pull_done and not self.meta_open and not self.out
                  and t[:1] in '"“' and not b['num'])
        if b['style'] == 'Intense Quote' or opener:
            self.close_meta()
            if not self.pull_done and not self.out:
                self.out.append(f'<div class="pull">{esc(t)}</div>')
                self.pull_done = True
            else:
                self.out.append(f'<blockquote class="v7-quote">{h}</blockquote>')
            return
        # chapter-opening labels → meta-row (Purpose / Principles / Benefits)
        if not self.seen_h2 and META.match(t):
            self.close_lists()
            if not self.meta_open:
                self.out.append('<div class="meta-row reveal" style="margin-top:14px; padding-top:16px;">')
                self.meta_open = True
            else:
                self.out.append('</div>')
            self.out.append(f'<div class="meta-item"><span class="eyebrow">{esc(t)}</span>')
            return
        lvl = b['lvl']
        if lvl == 6:
            self.close_meta()
            self.out.append(f'<p class="v7-disclaimer"><em>{esc(t)}</em></p>')
            return
        if lvl in (2, 3, 4, 5):
            self.close_meta()
            marker = b['num']['marker'] + ' ' if b['num'] and b['num']['marker'] else ''
            text = esc(marker + t)
            if lvl == 2:
                self.seen_h2 = True
                sid = f'{self.cid}-{len(self.subs) + 1}'
                self.subs.append((sid, marker + t))
                self.out.append(f'<h3 class="sub-title subhead" id="{sid}">{text}</h3>')
            elif lvl == 3:
                self.out.append(f'<h4 class="item-title">{text}</h4>')
            elif lvl == 4:
                self.out.append(f'<h5 class="item-title v7-h5">{text}</h5>')
            else:
                self.out.append(f'<h6 class="item-title v7-h6">{text}</h6>')
            return
        if b['num'] and b['num']['fmt'] != 'none':
            self.li(b)
            return
        if self.meta_open and not b['num']:
            # a free paragraph inside a meta block (e.g. "A robust … through:") stays inside it
            if self.list_stack or len(t) > 160 or not t.endswith(':'):
                self.close_meta()
            else:
                self.out.append(f'<p>{h}</p>')
                return
        self.close_lists()
        self.out.append(f'<p>{h}</p>')


# ───────────────────────────── chapters ─────────────────────────────
def split_chapters(D):
    """H1-delimited chunks; 'CHAPTER N' labels dropped (shown as the kicker)."""
    chunks, cur = [], None
    for b in D.blocks:
        if b['k'] == 'p' and b['style'] == 'Heading 1':
            cur = {'title': b['text'], 'blocks': []}
            chunks.append(cur); continue
        if b['k'] == 'p' and re.match(r'^CHAPTER\s+\d+$', b['text']):
            continue
        if cur is not None:
            cur['blocks'].append(b)
    return chunks


CH_MAP = [  # (docx H1, portal id, kicker, chapter number)
    ('Recruitment and Selection', 'ch3', 'CHAPTER 3', '3'),
    ('Compensation, Benefits and Incentive Policy', 'ch4', 'CHAPTER 4', '4'),
    ('Joining and Confirmation', 'ch5', 'CHAPTER 5', '5'),
    ('Learning and Development', 'ch6', 'CHAPTER 6', '6'),
    ('Performance Management', 'ch7', 'CHAPTER 7', '7'),
    ('Career Progression', 'ch8', 'CHAPTER 8', '8'),
    ('Employee Engagement, Rewards and Recognition', 'ch9', 'CHAPTER 9', '9'),
    ('Discipline and Conduct', 'ch10', 'CHAPTER 10', '10'),
    ('Employee Exit Management', 'ch11', 'CHAPTER 11', '11'),
    ('Organisation Policies', 'ch12', 'CHAPTER 12', '12'),
]


def article(cid, kicker, title, body):
    return (f'<article class="jx-chapter" id="chap-{cid}" hidden>\n'
            f'      <header class="jx-head"><div class="jx-head-row"><div><p class="jx-kicker">{esc(kicker)}</p>'
            f'<h1 class="jx-h1">{esc(title)}</h1></div></div></header>\n'
            f'      <section class="chap" id="{cid}">\n<div class="prose reveal">\n{body}\n</div>\n</section>\n    </article>')


def sub_num(label):
    m = re.match(r'^(\d+(?:\.\d+)*)\s+(.*)$', label.strip())
    return (m.group(1), m.group(2)) if m else ('', label.strip())


# ───────────────────────────── infographics ─────────────────────────────
# Wording inside V7's own images, transcribed verbatim (the image is the source).
IMG_LEARNER_JOURNEY = '27eb860c'
IMG_TMS_FLOW = '356c72a9'
IMG_TNA_TABLE = 'fc9e18c9'
IMG_CAL_FINAL = '4b87c084'
IMG_SAMPLE_PLAN = 'de0d0bbd'
IMG_LMS = 'f49625e6'
IMG_UNIFIED = 'd5ddab0d'
IMG_ABSENT = '597b4569'
# text printed in the Unified Apps image (About the Manual)
UNIFIED = ('Unified App’s', ['Recruitment Management System (RMS)', 'Training Management System (TMS)',
                             'Learning Management System (LMS)', 'Performance Management System (PMS)', 'SOP’s'])

LEARNER_JOURNEY = [
    {'title': 'Customer-facing roles',
     'subtitle': 'Sales Consultant | Sales Team Leader | Hostess | Customer Relationship Executive | Corporate Sales Executive | IDT | Sales Manager',
     'steps': [('Level 1', 'Within 30 days of joining'), ('Level 2', 'Within 90 days of joining'), ('Level 3', 'Within 180 days of joining')],
     'chips': ['Level 1 Certification Assessment', 'Level 2 Certification Assessment', 'Level 3 Certification Assessment']},
    {'title': 'All other roles', 'subtitle': 'Every other role in the dealership',
     'steps': [('Role-specific training', '30 days of joining'), ('Refresher Trainings', 'Run through the year as per the training calendar')],
     'chips': ['Role-specific Training Assessment']},
]
TMS_FLOW = ('Training Process Flow in TMS for JSW Trainings', [
    ('Step 1 — Training Calendar Release', 'JSW Motors releases monthly training calendar & nominates dealer manpower'),
    ('Step 2 — Nomination Confirmation', 'Nomination available on Training Management System to respective IDT for review & confirmation'),
    ('Step 3 — Attend Scheduled Training', 'Confirmed manpower attends scheduled training at venue'),
    ('Step 4 — Attendance Capture', 'Attendance marked digitally in TMS by the trainee under Trainer’s Supervision'),
    ('Step 5 — Pre & Post Training Assessment', 'Pre & Post training assessment conducted digitally on Training Management System'),
    ('Step 6 — Results Published & Visibility', 'Assessment results generated & published in real-time, immediate visibility for Trainers & Dealers'),
    ('Step 7 — Training Feedback', 'Feedback is captured to measure participant satisfaction and learning experience'),
])
TNA_TABLE = ('TNA Process', ['Parameter', 'Methods', 'Applicable Category'], [
    ('Knowledge Check', 'Assessments', ['Product', 'Process']),
    ('Performance Check', 'Data on — Sales funnel: Enquiry → Booking → Retail, Test Drive Ratio, Demo observations', ['Product', 'Process']),
    ('Training Gaps', 'Score gaps in LMS-assigned modules to Dealership role holders', ['Product', 'Process']),
    ('SOP Adherence', 'Customer Journey Gaps through On-Job Observation (OJO) by IDT', ['Process', 'Soft Skills']),
    ('Complaints', 'Data on — SSI Score, number of complaints logged, Customer Satisfaction', ['Soft Skills']),
    ('Follow-up Quality', 'Follow-up done / not done tracking through Log review', ['Soft Skills']),
])
CAL_FINAL = ('Training Calendar Finalization Process For Internal Dealer Trainer (IDT)', [
    ('TNA Report (Input)', ['Inputs for', '1. Product, Process & Soft Skills Trainings', 'Avoid – assuming needs without data & Validation',
                            'Timelines – By 20th of every Month']),
    ('Calendar Draft Preparation & Nomination Confirmation', ['Create training calendar 6A basis to TNA inputs using form',
                            'Define: Topics | Mode | Duration | Date I Targeted nomination', 'Nominate participants and inform respective reporting manager',
                            'Avoid - Peak sales/festive periods', 'Timelines – Between 21st to 23rd of every Month']),
    ('GM Discussion & Approval', ['Present calendar to GM & Incorporate Feedback if any', 'Adjust dates if there are any conflicts',
                            'Get formal sign-off from GM', 'Timelines – by 24th of every month']),
    ('Calendar Rollout', ['Email to GM, Reporting manager & nominated participants & Display on notice board with Nominations',
                            'Share through digital platforms within dealership', 'Communicate changes as and when required', 'Timelines – 25th of Every Month']),
    ('Conduct Training', ['Conduct training as per schedule', 'Maintain attendance & Photos/documentation for records',
                            'Avoid – starting sessions without pre-training readiness checks – Reading material, attendance sheet, content readiness',
                            'Timelines – 1st to 3rd Week of every month']),
    ('Post-Training Assessment', ['Conduct post-test', 'Evaluate and record Scores', 'Update Dealership training records', 'Timelines – On the training day']),
    ('Feedback Collection', ['Take participant feedback using feedback form 6B', 'Avoid – Not evaluating feedback and taking corrective actions',
                            'Timelines – On the training day']),
    ('Records & Documentation', ['Record attendance & assessment scores', 'Maintain training & certification records',
                            'Avoid – Closing the cycle without updating all records and documenting key learnings']),
])
SAMPLE_PLAN = ('Sample Training Calendar – Week Wise Plan', ['Week', 'Topic/Modules', 'Coverage'], [
    (['Week 1', 'Product Orientation Training'], ['New Product Introduction', 'Key Features', 'USPs & Competitive Edge', 'Product Demo Techniques', 'Field Application'],
     ['Product line-up overview, model range & variants, brand positioning', 'Technical specifications, feature walkthrough, segment-wise comparison',
      'Unique selling propositions, competitor comparison', 'Walkaround demo practice, demo scripts', 'Showroom display standards, demo vehicle etiquette',
      'Written quiz + verbal product pitch evaluation']),
    (['Week 2', 'Process Knowledge'], ['Sales Process Overview', 'Customer Inquiry Handling', 'Test Drive & Delivery Process', 'Finance & Insurance', 'Documentation & Reporting'],
     ['End-to-end sales funnel, lead stages, CRM', 'Inquiry logging, follow-up cadence, prospect categorization', 'Test drive SOP’s, delivery ceremony',
      'Insurance, accessories, finance documentation', 'CRM data entry, escalation matrix', 'Process simulation roleplay']),
    (['Week 3', 'Soft Skills & Behavioral Training'], ['Communication Skills', 'Customer Handling', 'Negotiation Skills', 'Objection Handling', 'Presentation & Confidence Building'],
     ['Negotiation framework, value vs. price conversations, closing techniques', 'Common objections bank,  de-escalation tactics',
      'Public speaking, product storytelling, mock presentations']),
])
LMS_STEPS = [('Publish', 'Training team publishes a plan for each role holder'), ('Assign', 'Users see only content that fits their role'),
             ('Learn', "Modules, videos, PDFs and Web based trainings (WBT's)"), ('Assess', 'Online quizzes and knowledge checks'),
             ('Track', 'Progress and scores visible to user and management')]


def tna_table_html(title, head, rows):
    cats = {'Product': 'v7-cat-product', 'Process': 'v7-cat-process', 'Soft Skills': 'v7-cat-soft'}
    body = ''.join(f'<tr><td><strong>{esc(p)}</strong></td><td>{esc(m)}</td><td>'
                   + ''.join(f'<span class="v7-cat {cats[c]}">{esc(c)}</span>' for c in cs) + '</td></tr>' for p, m, cs in rows)
    return (f'<h5 class="item-title v7-h5">{esc(title)}</h5><div class="table-wrap"><table><thead><tr>'
            + ''.join(f'<th>{esc(h)}</th>' for h in head) + f'</tr></thead><tbody>{body}</tbody></table></div>')


def plan_table_html(title, head, rows):
    ul = lambda xs: '<ul class="cell-bullets">' + ''.join(f'<li>{esc(x)}</li>' for x in xs) + '</ul>'
    body = ''.join(f'<tr><td><strong>{esc(w[0])}</strong><br>{esc(w[1])}</td><td>{ul(t)}</td><td>{ul(c)}</td></tr>' for w, t, c in rows)
    return (f'<h5 class="item-title v7-h5">{esc(title)}</h5><div class="table-wrap"><table><thead><tr>'
            + ''.join(f'<th>{esc(h)}</th>' for h in head) + f'</tr></thead><tbody>{body}</tbody></table></div>')


def calendar_events(D, chunks):
    """Every dated item V7 gives, as calendar rules. Titles/descriptions are V7 text."""
    def table_rows(title, first):
        for b in chunks[title]['blocks']:
            if b['k'] == 'tbl' and b['t'].rows[0].cells[0].text.strip() == first:
                return [[c.text.strip() for c in cells_of(r)] for r in b['t'].rows]
        raise KeyError(first)
    E = []
    eng = table_rows('Employee Engagement, Rewards and Recognition', 'Activity')
    for act, guide, purpose, by, att in eng[1:]:
        when = guide.split('When – ')[-1].strip()
        rule = None
        if '1st week of the next month' in when: rule = {'m': 'all', 'day': None}
        elif '7th April' in when: rule = {'m': 3, 'day': 7}
        elif '2nd October' in when: rule = {'m': 9, 'day': 2}
        if rule:
            E.append({**rule, 'title': act.replace('\n', ' '), 'category': 'engagement', 'freq': guide.replace('\n', ' · ').strip(' ·'),
                      'audience': att, 'chapter': 'ch9-1', 'chapterLabel': 'Ch.9 · 9.1 Employee Engagement Activities',
                      'desc': f'Purpose: {purpose} · Arranged by: {by}'})
    E.append({'m': 11, 'day': None, 'title': 'Employee Engagement Calendar is published', 'category': 'engagement',
              'freq': 'December month of the previous year', 'audience': 'All', 'chapter': 'ch9-1',
              'chapterLabel': 'Ch.9 · 9.1 Employee Engagement Activities',
              'desc': 'Employee Engagement Calendar is published in December month of the previous year on digital platforms and also placed on the notice board'})
    monthly =[b for b in chunks['Employee Engagement, Rewards and Recognition']['blocks'] if b['k'] == 'tbl'
               and b['t'].rows[0].cells[0].text.strip() == 'Award']
    for blk in monthly:
        rows = [[c.text.strip() for c in cells_of(r)] for r in blk['t'].rows]
        hdr = rows[0]
        wi = next(i for i, h in enumerate(hdr) if h.startswith('When to give award'))
        ri = next(i for i, h in enumerate(hdr) if h.startswith('Applicable') or h.startswith('Roleholders'))
        for r in rows[1:]:
            when = r[wi].replace('\n', ' ')
            m = re.match(r'(1st|3rd) Friday of the (N\+1 month|1st month of the N\+1 QTR)', when)
            if not m:
                continue
            n = 1 if m.group(1) == '1st' else 3
            # "N+1 month" → every month; "1st month of the N+1 QTR" → Jan/Apr/Jul/Oct (V7: Q1 2026 awards in April 2026)
            months = 'all' if 'N+1 month' in when else [0, 3, 6, 9]
            E.append({'m': months, 'nth': [n, 5], 'day': None, 'title': r[0].replace('\n', ' '), 'category': 'recognition',
                      'freq': when, 'audience': r[ri].replace('\n', ' '), 'chapter': 'ch9-2',
                      'chapterLabel': 'Ch.9 · 9.2 Rewards and Recognition', 'desc': r[1].replace('\n', ' ')})
    inc = table_rows('Compensation, Benefits and Incentive Policy', 'Date')
    for date, act, who in inc[1:]:
        day = int(re.search(r'\d+', date).group(0))
        E.append({'m': 'all', 'day': day, 'title': act, 'category': 'incentive', 'freq': f'{date} of every month',
                  'audience': who, 'chapter': 'ch4-4', 'chapterLabel': 'Ch.4 · 4.4 Incentive Scheme',
                  'desc': 'It is a monthly performance reward program for achieving business targets.'})
    rev_desc = 'Two weeks before the review is due, HR should remind the reporting manager to conduct the review meeting'
    for m, t in ((5, 'Quarterly reviews are held in June and December'), (11, 'Quarterly reviews are held in June and December'),
                 (8, 'Mid-year review is held in September'), (2, 'Annual review is held in March')):
        E.append({'m': m, 'day': None, 'title': t, 'category': 'reviews', 'freq': 'For April to March cycle', 'audience': 'Employee, Reporting Manager, HR Manager',
                  'chapter': 'ch7-1', 'chapterLabel': 'Ch.7 · 7.1 Career Driven Performance Management', 'desc': rev_desc})
    for day, head, bullets in ((20, *CAL_FINAL[1][0]), (21, *CAL_FINAL[1][1]), (24, *CAL_FINAL[1][2]), (25, *CAL_FINAL[1][3])):
        E.append({'m': 'all', 'day': day, 'title': head, 'category': 'training', 'freq': bullets[-1], 'audience': 'IDT',
                  'chapter': 'ch6-3', 'chapterLabel': 'Ch.6 · 6.3 Monthly In-house Training Calendar Planning Process',
                  'desc': ' · '.join(bullets[:-1])})
    head, bullets = CAL_FINAL[1][4]
    E.append({'m': 'all', 'day': None, 'title': head, 'category': 'training', 'freq': bullets[-1], 'audience': 'IDT',
              'chapter': 'ch6-3', 'chapterLabel': 'Ch.6 · 6.3 Monthly In-house Training Calendar Planning Process', 'desc': ' · '.join(bullets[:-1])})
    return E


def phone_fallback(card, lines):
    """Canvas diagrams scale to the screen; under 600px their text is unreadable, so phones get V7's points as a list."""
    card = card.replace('class="jsw-interactive-card', 'class="v7-desk jsw-interactive-card', 1)
    return card + '<ul class="list-clean v7-phone">' + ''.join(f'<li>{x}</li>' for x in lines) + '</ul>'


def make_hooks(T, D, chunks):
    import infographics as G
    texts_after = lambda blocks, i, n: [blocks[i + 1 + k]['text'] for k in range(n)]

    def hook(R, blocks, i):
        b = blocks[i]
        cid = R.cid
        if b['k'] == 'tbl':
            first = b['t'].rows[0].cells[0].text.strip()
            if cid == 'ch8' and first == 'Work Area':
                rows = [[c.text.strip() for c in cells_of(r)] for r in b['t'].rows]
                nxt = blocks[i + 1]['text'] if i + 1 < len(blocks) else ''
                cap, _, note = nxt.partition('\n')
                assert cap.startswith('Chart 8.1')
                return G.career_matrix(T, rows, cap.strip()) + (f'\n<p>{esc(note.strip())}</p>' if note.strip() else ''), 2
            if cid == 'ch9' and first == 'Month':
                rows = [[c.text.strip() for c in cells_of(r)] for r in b['t'].rows][1:]
                assert len(rows) == 12
                themes = [(t, p, a) for _, t, p, a in rows]
                return G.calendar(T, themes, calendar_events(D, chunks)), 1   # the annual view carries every cell of 9.1.2
            return None
        t = b['text']
        if b['imgs']:
            h = b['imgs'][0][3]
            tail = f'<p>{b["html"]}</p>' if t else ''
            if h == IMG_LEARNER_JOURNEY: return fc.learner_journey(LEARNER_JOURNEY) + tail, 1
            if h == IMG_TMS_FLOW: return fc.vlist(TMS_FLOW[0], TMS_FLOW[1]) + tail, 1
            if h == IMG_TNA_TABLE: return tna_table_html(*TNA_TABLE) + tail, 1
            if h == IMG_CAL_FINAL: return fc.module_snake(*CAL_FINAL) + tail, 1
            if h == IMG_SAMPLE_PLAN: return plan_table_html(*SAMPLE_PLAN) + tail, 1
            if h == IMG_UNIFIED: return fc.unified(*UNIFIED) + tail, 1
            if h == IMG_ABSENT: return fc.absent_flow() + tail, 1
            if h == IMG_LMS: return fc.chevrons(LMS_STEPS) + tail, 1
            return None
        if cid == 'ch6' and t == 'i. Training delivery coverage':
            a, b2 = texts_after(blocks, i, 2), blocks[i + 3]
            assert b2['text'] == 'ii. Effectiveness'
            c = texts_after(blocks, i + 3, 2)
            return fc.ring(['What IDT', 'reports'], [(t, a), (b2['text'], c)]), 6
        if cid == 'ch7' and t == 'Follow the SMART framework while setting KPIs:':
            rows = []
            for x in texts_after(blocks, i, 5):
                l, w, d = [p.strip() for p in re.split(r'\s+–\s+', x, maxsplit=2)]
                rows.append((l, w, d))
            return f'<p>{b["html"]}</p>' + fc.smart(rows), 6
        if cid == 'ch7' and t == 'Review performance expectations against the set KPIs:':
            return f'<p>{b["html"]}</p>' + fc.review(texts_after(blocks, i, 4)), 5
        if cid == 'ch9' and t.startswith('Managers should immediately recognise'):
            return f'<p>{b["html"]}</p>' + fc.spot(texts_after(blocks, i, 3), 'SPOT'), 4
        return None
    return hook


def build():
    base = subprocess.run(['git', 'show', f'{BASE_COMMIT}:v2.html'], cwd=REPO, capture_output=True,
                          text=True, check=True).stdout
    D = Doc(DOCX)
    chunks = {c['title']: c for c in split_chapters(D)}
    sys.path.insert(0, str(Path(__file__).parent))
    from infographics import Templates
    Renderer.hooks = make_hooks(Templates(base), D, chunks)
    toc_subs, annex_all = {}, []

    # ── intro pages ───────────────────────────────────────────────
    fm_i = Renderer(D, 'fm-i')
    parts = []
    for name in ('JSW Group', 'JSW Motors'):
        parts.append(f'<h3 class="sub-title subhead"{" style=\"margin-top:0\"" if name == "JSW Group" else ""}>{esc(name)}</h3>')
        fm_i.out = []
        fm_i.render(chunks[name]['blocks'])
        # inside JSW Group / JSW Motors, V7's "Our Purpose / Our Vision …" sit one level below the group name
        part = '\n'.join(fm_i.out)
        part = re.sub(r'<h3 class="sub-title subhead" id="fm-i-\d+">(.*?)</h3>', r'<h4 class="item-title">\1</h4>', part)
        parts.append(part)
    fm_i_html = article('fm-i', 'i.', 'JSW Group and JSW Motors Vision and Foundation', '\n'.join(parts))

    # Message from Management: keep the existing photo beside Option 1
    m_img = re.search(r'<div class="col-media">.*?</div>\s*</div>\s*</div>', base[base.find('id="chap-fm-i"'):], re.S).group(0)
    msg = []
    for n in (1, 2, 3):
        key = f'Message from Management (Option {n})'
        r = Renderer(D, 'fm-ii'); r.render(chunks[key]['blocks'])
        body = '\n'.join(r.out)
        # [Name] / [Designation] / JSW Motors → existing sign-off block
        sig = re.search(r'<p>\[Name\]</p>\s*<p>\[Designation\]</p>\s*<p>(JSW Motors)\s*</p>\s*$', body)
        if sig:
            body = body[:sig.start()] + ('<div class="signoff"><div class="sig-line"></div><div class="sig-name">[Name]</div>'
                                         '<div class="sig-role">[Designation]</div><div class="sig-org">JSW Motors</div></div>')
        head = f'<h3 class="sub-title subhead"{" style=\"margin-top:0\"" if n == 1 else ""}>{esc(key)}</h3>'
        if n == 1:
            msg.append(f'<div class="split-grid"><div class="col-text">{head}\n{body}\n</div>\n{m_img}')
        else:
            msg.append(f'{head}\n{body}')
    fm_ii_html = article('fm-ii', 'ii.', 'Message from Management', '\n'.join(msg))

    r = Renderer(D, 'fm-iii'); r.render(chunks['About the Manual']['blocks'])
    about = '\n'.join(r.out)
    about = about.replace('<p><strong>Introduction to Unified Apps</strong></p>', '<h3 class="sub-title subhead">Introduction to Unified Apps</h3>')
    assert 'Introduction to Unified Apps</h3>' in about
    fm_iii_html = article('fm-iii', 'iii.', 'About the Manual', about)

    # ── chapters 3-12 ─────────────────────────────────────────────
    arts = []
    for title, cid, kicker, n in CH_MAP:
        r = Renderer(D, cid)
        body = r.render(chunks[title]['blocks'])
        arts.append(article(cid, kicker, title, body))
        toc_subs[cid] = r.subs
        annex_all.append((n, title, r.annex))

    # ── annexure (consolidated from the chapters' own ANNEXURE lists) ──
    jd_annex = [('2A', 'Job Description Template'), ('2B', 'All Job Descriptions'), ('2C', 'Competencies')]
    annex_all.insert(0, ('2', 'Job Descriptions', jd_annex))
    ab = []
    for n, title, items in annex_all:
        if not items:
            continue
        ab.append(f'<h3 class="sub-title subhead" id="annex-{n}">{esc(n + ". " + title)}</h3>')
        ab.append('\n'.join(annex_html(c, t) for c, t in items))
    annex_html_ = article('annexure', 'ANNEXURE', 'Annexures', '\n'.join(ab))

    # ── splice ────────────────────────────────────────────────────
    a = base.find('    <article class="jx-chapter" id="chap-fm-i"')
    b = base.find('    <article class="jx-chapter" id="chap-ch2"')
    c = base.find('    <article class="jx-chapter" id="chap-ch3"')
    e = base.find('</article>', base.find('id="chap-annexure"')) + len('</article>')
    assert 0 < a < b < c < e
    mid = base[b:c]
    mid = patch_ch1_ch2(mid, D, chunks, toc_subs)
    html_out = (base[:a] + '    ' + fm_i_html + '\n    ' + fm_ii_html + '\n    ' + fm_iii_html + '\n' + mid
                + '    ' + '\n    '.join(arts) + '\n    ' + annex_html_ + base[e:])

    # chapters 3-12 + annexure stay locked (base routing/nav guards) until the user releases them; only i-iii, 1, 2 are open
    assert html_out.count("['i', 'ii', 'iii', '1', '2'].indexOf(ch.num) === -1") == 2
    # groups lost their "Part X · " prefix (ab1bffd), so short === name and the sidebar printed it twice
    dup = "g.name ? '<b>' + esc(g.short) + '</b><span>' + esc(g.name) + '</span>'"
    assert html_out.count(dup) == 1
    html_out = html_out.replace(dup, "g.name && g.name !== g.short ? '<b>' + esc(g.short) + '</b><span>' + esc(g.name) + '</span>'")
    # X and XPlus share one chart but get their own tab each
    tabs = "        window.ORG_CATEGORIES.forEach(function(cat, i){\n          var btn = document.createElement('button');"
    assert html_out.count(tabs) == 1
    html_out = html_out.replace(tabs, "        (function(a){ var x = a[0]; a.splice(0, 1, Object.assign({}, x, {label: 'X Category'}), Object.assign({}, x, {label: 'XPlus Category'})); })(window.ORG_CATEGORIES);\n" + tabs)
    # one chapter-opening order, as in the docx: Purpose, then Principles, then the two Benefit lists
    html_out = reorder_openers(html_out)
    # reading emphasis — markup only; text content must be byte-identical
    import readability
    a = html_out.find('    <article class="jx-chapter" id="chap-fm-i"')
    e = html_out.find('</article>', html_out.find('id="chap-annexure"')) + len('</article>')
    region, stats, leads = readability.emphasize(html_out[a:e])
    strip = lambda x: re.sub(r'<[^>]+>', '', x)
    assert strip(region) == strip(html_out[a:e]), 'emphasis changed text'
    html_out = html_out[:a] + region + html_out[e:]
    print('emphasis', stats)
    if '--leads' in sys.argv:
        print('\n'.join(sorted(set(leads))))
    html_out = link_steps(html_out)
    html_out = patch_home(html_out)
    html_out = patch_toc(html_out, toc_subs)
    html_out = inject_css(html_out)
    html_out = finish(html_out)
    OUT.write_text(html_out)
    print('wrote', OUT, len(html_out))




def _gray(r, g, b):
    import colorsys
    hh, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return s > 0.3 and 0.04 < l < 0.98, round(0.299 * r + 0.587 * g + 0.114 * b)


def desaturate(h):
    """Gold / red / green / purple literals -> neutral grey of the same lightness (house palette is greyscale)."""
    def hx(m):
        x = m.group(1)
        x = ''.join(c * 2 for c in x) if len(x) == 3 else x
        hit, y = _gray(*(int(x[i:i + 2], 16) for i in (0, 2, 4)))
        return '#%02X%02X%02X' % (y, y, y) if hit else m.group(0)
    def rg(m):
        hit, y = _gray(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return 'rgb%s(%d, %d, %d%s)' % (m.group(0)[3:4] if m.group(0)[3:4] == 'a' else '', y, y, y, m.group(4) or '') if hit else m.group(0)
    h = re.sub(r'(?<![\w&])#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b(?![\w-])', hx, h)
    return re.sub(r'rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(,\s*[\d.]+)?\)', rg, h)


def _principles_block(h, i):
    """end index of a body-level 'Principles' block starting at the <h3> at i (Ch.1 / Ch.2 openers)."""
    j = h.index('</h3>', i) + 5
    k = re.compile(r'\s*').match(h, j).end()
    if h.startswith('<ul', k):
        return h.index('</ul>', k) + 5
    assert h.startswith('<p>', k)
    p_end = h.index('</p>', k) + 4
    d = re.compile(r'\s*').match(h, p_end).end()
    assert h.startswith('<div class="row-2col"', d)
    return _div_end(h, d)


def reorder_openers(h):
    row_re = re.compile(r'<div class="meta-row reveal"[^>]*>')
    out, pos, n = [], 0, 0
    for m in row_re.finditer(h):
        if m.start() < pos:
            continue
        end = _div_end(h, m.start())
        items = re.findall(r'<div class="meta-item">.*?</div>', h[m.end():end], re.S)
        purpose = [x for x in items if '<span class="eyebrow">Purpose:</span>' in x or '<span class="eyebrow">PURPOSE:</span>' in x]
        pr = [x for x in items if re.search(r'<span class="eyebrow">Principles:</span>', x)]
        rest = [x for x in items if x not in pr and x not in purpose]
        if not purpose:
            continue
        row = lambda xs: m.group(0).replace('style="', 'style="grid-template-columns:1fr;', 1) if False else m.group(0)
        solo = m.group(0)[:-1] + ' data-solo="1">' if 'style=' not in m.group(0) else re.sub(r'style="', 'data-solo="1" style="', m.group(0), 1)
        if pr:
            body = re.sub(r'<div class="meta-item"><span class="eyebrow">Principles:</span>\s*(.*)</div>$', r'\1', pr[0].strip(), flags=re.S)
            princ = '\n<h3 class="sub-title subhead">Principles</h3>\n' + body
            tail_from = end
        else:
            k = re.compile(r'\s*').match(h, end).end()
            if not h.startswith('<h3 class="sub-title subhead">Principles</h3>', k):
                continue
            tail_from = _principles_block(h, k)
            princ = '\n' + h[k:tail_from]
        out.append(h[pos:m.start()] + solo + ''.join(purpose) + '</div>' + princ + '\n' + m.group(0) + ''.join(rest) + '</div>')
        pos = tail_from
        n += 1
    out.append(h[pos:])
    print('openers reordered', n)
    return ''.join(out)


CALC = '''<div class="mp-calc" id="mpCalc">
<table class="mp-table"><thead><tr><th>Sales Manpower Productivity (Month)</th><th><input id="mpVol" type="number" min="0" step="1" inputmode="numeric" placeholder="ENTER NUMBER" aria-label="Enter your outlet's monthly sales target"></th><th>Manpower required</th><th>Salary (&#8377;)</th></tr></thead><tbody>
@@ROWS@@
</tbody><tfoot><tr><td colspan="2">Total Manpower Required / Total Fixed Cost (Salaries)</td><td><b id="mpTot">&mdash;</b></td><td><b id="mpCost">&mdash;</b></td></tr></tfoot></table>
</div>
<script>
(function(){
  /* formulae and salary rates from "Ch1 manpower calculator.xlsx" */
  var rows = document.querySelectorAll('#mpCalc tr[data-role]');
  var vol = document.getElementById('mpVol');
  function fmt(n){ return (Math.round(n * 100) / 100).toLocaleString('en-IN', {maximumFractionDigits: 2}); }
  function calc(){
    var t = parseFloat(vol.value), ok = isFinite(t) && t > 0;
    var C = {};
    C.cons = t / 4;
    C.tl = C.cons / 5;
    C.sm = t > 1 ? Math.max(C.tl / 5, 1) : C.tl / 5;
    C.cre = t > 1 ? Math.max(t / 50, 1) : t / 50;
    C.fi = t > 1 ? Math.max(t / 50, 1) : t / 50;
    C.rd = t / 50;
    C.crm = C.cre / 3;
    var men = 0, cost = 0;
    rows.forEach(function(tr){
      var n = C[tr.dataset.role], sal = n * parseFloat(tr.dataset.sal);
      tr.querySelector('.mp-n').textContent = ok ? fmt(n) : 'X';
      tr.querySelector('.mp-c').textContent = ok ? fmt(sal) : '—';
      if(ok){ men += n; cost += sal; }
    });
    document.getElementById('mpTot').textContent = ok ? fmt(men) : '—';
    document.getElementById('mpCost').textContent = ok ? fmt(cost) : '—';
  }
  vol.addEventListener('input', calc);
  calc();
})();
</script>'''

CALC_ROWS = [('cons', 'No. Sales Consultants required', 40000), ('tl', 'No. of Team Leaders required', 55000),
             ('sm', 'No. of Sales Managers required', 100000), ('cre', 'No. of CREs required', 22500),
             ('fi', 'No. of Car Finance &amp; Insurance Executives required', 27000),
             ('rd', 'No. of Car Registration &amp; Delivery Executives required', 22500),
             ('crm', 'No. of CRM Sales required', 45000)]


def calculator(h):
    pat = re.compile(r'<div class="table-wrap"><table><thead><tr><th><strong>Sales Manpower Productivity \(Month\)</strong></th>.*?</table></div>', re.S)
    assert len(pat.findall(h)) == 1
    rows = ['<tr data-role="%s" data-sal="%d"><td>%s</td><td class="mp-n">X</td><td class="mp-n">&mdash;</td><td class="mp-c">&mdash;</td></tr>' % (k, sal, label) for k, label, sal in CALC_ROWS]
    # columns: label | (input col) | manpower | salary -> keep the input column empty in body rows
    rows = [r.replace('<td class="mp-n">X</td><td class="mp-n">&mdash;</td>', '<td></td><td class="mp-n">X</td>') for r in rows]
    return pat.sub(lambda m: CALC.replace('@@ROWS@@', '\n'.join(rows)), h)


MP_CSS = '''
.mp-calc{margin:14px 0 8px}
.mp-table{width:100%;border-collapse:collapse;font-size:15px}
.mp-table th,.mp-table td{border:1px solid var(--border,#d2d2d2);padding:10px 12px;text-align:left;vertical-align:middle}
.mp-table thead th{background:var(--ink,#1b1b1d);color:#fff;font-weight:600}
.mp-table tfoot td{font-weight:600;background:rgba(0,0,0,.04)}
.mp-table input{width:100%;min-width:90px;padding:7px 9px;border:1px solid #b1b1b1;border-radius:6px;font:inherit;background:#fff;color:#1b1b1d}
.mp-table thead input{font-weight:600}
.mp-table .mp-n{font-weight:700;text-align:center;width:90px}
.mp-per{display:inline-flex;align-items:center;gap:6px;margin-left:10px;color:#46474c;font-size:13px}
.mp-per input{width:64px;min-width:0}
.mp-note{margin-top:10px;font-size:13px;color:#46474c;max-width:none}
.jx-lc{text-transform:none!important;letter-spacing:0!important}
.meta-row[data-solo]{grid-template-columns:1fr!important}
@media(max-width:720px){.mp-table{display:block;overflow-x:auto}}
'''


FX_CSS = '''
.fx-node:not(.fx-link){cursor:pointer}
.fx-node.fx-on{outline:2px solid #1b1b1d;outline-offset:3px;box-shadow:0 6px 18px rgba(0,0,0,.18);transition:box-shadow .2s}
.fx-node:focus-visible{outline:2px solid #1b1b1d;outline-offset:3px}
'''
FX_JS = '''<script>
(function(){
  /* flow steps that have no heading to jump to: click / Enter / Space to highlight the step */
  function nodes(){ document.querySelectorAll('.fx-node:not(.fx-link)').forEach(function(n){ n.tabIndex = 0; n.setAttribute('role','button'); n.setAttribute('aria-pressed','false'); }); }
  function pick(n){
    var f = n.closest('.fx-flow') || n.parentNode, on = n.classList.contains('fx-on');
    f.querySelectorAll('.fx-node.fx-on').forEach(function(x){ x.classList.remove('fx-on'); x.setAttribute('aria-pressed','false'); });
    if(!on){ n.classList.add('fx-on'); n.setAttribute('aria-pressed','true'); }
  }
  document.addEventListener('click', function(e){ var n = e.target.closest('.fx-node:not(.fx-link)'); if(n && !e.target.closest('a')) pick(n); });
  document.addEventListener('keydown', function(e){ if(e.key !== 'Enter' && e.key !== ' ') return; var n = e.target.closest && e.target.closest('.fx-node:not(.fx-link)'); if(n && n === e.target){ e.preventDefault(); pick(n); } });
  nodes();
})();
</script>'''


def finish(h):
    # colours and graphs left as approved
    h = calculator(h)
    # "Annexure", not ANNEXURE (headings, chapter sub-lists, sidebar group, viewer modal)
    h = h.replace('<strong style="color:var(--ink)">ANNEXURE</strong>', '<strong style="color:var(--ink)">Annexure</strong>')
    h = h.replace('<h4 class="subhead" style="font-weight:700;margin-bottom:12px;">ANNEXURE</h4>', '<h4 class="subhead" style="font-weight:700;margin-bottom:12px;">Annexure</h4>')
    h = h.replace('<p class="jx-kicker">ANNEXURE</p>', '<p class="jx-kicker jx-lc">Annexure</p>')
    h = h.replace("{group:'ANNEXURE'", "{group:'Annexure'")
    h = h.replace('OFFICIAL ANNEXURE VIEWER', 'Official Annexure Viewer').replace('<div style="display:none">ANNEXURE ', '<div style="display:none">Annexure ')
    old = "'<b>' + esc(g.short) + '</b>'));"
    assert h.count(old) == 1
    h = h.replace(old, "'<b' + (g.short === 'Annexure' ? ' class=\"jx-lc\"' : '') + '>' + esc(g.short) + '</b>'));")
    h = h.replace('</head>', '<style id="jx-mp">' + MP_CSS + FX_CSS + '</style></head>', 1)
    h = h.replace('</body>', FX_JS + '</body>', 1)
    return h


def patch_ch1_ch2(mid, D, chunks, toc_subs):
    """Ch.1 keeps its interactive org chart; add V7's numbering and §1.2 verbatim."""
    old = '<h3 class="sub-title subhead" id="ch2-1">Recommended Organisation Chart</h3>'
    assert old in mid
    mid = mid.replace(old, '<h3 class="sub-title subhead" id="ch2-1">1.1 Recommended Organisation Chart</h3>')
    # chapter quotes carry a closing full stop in V7
    for q in ('Structure follows strategy', 'A good job description tells you what success looks like, not just what tasks to perform'):
        assert f'<div class="pull">&quot;{q}&quot;</div>' in mid
        mid = mid.replace(f'<div class="pull">&quot;{q}&quot;</div>', f'<div class="pull">&quot;{q}.&quot;</div>')
    # V7 titles this role "CEO" (it reports to the Dealer Principal); other JDs keep "Dealer Principal / CEO" as their reporting line
    for a, b in (('<h3 class="rd-detail-title">Dealer Principal / CEO</h3>', '<h3 class="rd-detail-title">CEO</h3>'),
                 ('<span class="rd-role-name">Dealer Principal / CEO</span>', '<span class="rd-role-name">CEO</span>')):
        assert a in mid
        mid = mid.replace(a, b)
    # Ch.2 (JDs) heads its list "Benefit to Customer:" in V7
    k = mid.find('<article class="jx-chapter" id="chap-ch1"')
    lab = '<span class="eyebrow">BENEFIT TO CUSTOMERS:</span>'
    assert mid.count(lab, k) == 1
    mid = mid[:k] + mid[k:].replace(lab, '<span class="eyebrow">BENEFIT TO CUSTOMER:</span>')
    for lab in ('Role Clarity', 'Efficient Decision Making', 'Enhanced Collaboration', 'Resource Optimization'):
        a = f'font-weight:700;">{lab}</h4>'
        assert mid.count(a) == 1
        mid = mid.replace(a, f'font-weight:700;">{lab}:</h4>')
    blocks = chunks['Dealership Organisation Structure']['blocks']
    k = next(i for i, b in enumerate(blocks) if b['k'] == 'p' and b['text'].startswith('1.2 Build My Organisation'))
    r = Renderer(D, 'ch2'); r.subs = [('ch2-1', '1.1 Recommended Organisation Chart')]; r.seen_h2 = True
    sec = r.render(blocks[k:])
    toc_subs['ch2'] = r.subs
    end = mid.rfind('</section>', 0, mid.find('<article class="jx-chapter" id="chap-ch1"'))
    # §1.2 must be a direct child of .prose for paging: insert before prose closes
    pclose = mid.rfind('</div>', 0, end)
    mid = mid[:pclose] + sec + '\n' + mid[pclose:]
    return mid


def patch_home(h):
    h = h.replace('<li style="--i:4"><b>T</b>eamwork for Customers</li>', '<li style="--i:4"><b>T</b>eamwork</li>')
    h = h.replace('<p class="jx-hero-eyebrow">JSW Motors · Dealer Partner Network · Operating Standards</p>\n', '')
    h = h.replace('</ul>\n      </div>\n\n\n\n      <div class="jx-seg"',
                  '</ul>\n        <p class="jx-hero-quote">“Building a dealership network our customers can trust.”</p>\n      </div>\n\n\n\n      <div class="jx-seg"', 1)
    h = h.replace('<p>JSW HR Operations Manual &mdash; Dealer Partner Network Operating &amp; Governance Guide. For internal review.</p>',
                  '<p>TRUST: JSW HR Operations Manual</p>')
    assert 'jx-hero-quote' in h and 'Teamwork for Customers' not in h
    return h


def js(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


def patch_toc(h, subs):
    def item(cid, num, label, s=None):
        line = f"    {{id:'{cid}', num:'{num}', label:'{js(label)}', live:true"
        if s:
            line += ', subs:[\n' + ',\n'.join(
                f"      {{id:'{sid}', num:'{sub_num(l)[0]}', label:'{js(sub_num(l)[1])}'}}" for sid, l in s) + '\n    ]'
        return line + '}'
    def fix_nums(cid, s):
        # headings without a printed number (e.g. "Best Practice") get the next number for the menu only
        out, n = [], 0
        for sid, l in s:
            num, lab = sub_num(l)
            n += 1
            out.append((sid, l if num else f'{cid[2:]}.{n} {lab}'))
        return out
    S = {k: fix_nums(k, v) for k, v in subs.items()}
    toc = ("window.JX_TOC = [\n  {group:'Introduction', items:[\n"
           + item('fm-i', 'i', 'JSW Group and JSW Motors Vision and Foundation') + ',\n'
           + item('fm-ii', 'ii', 'Message from Management') + ',\n'
           + item('fm-iii', 'iii', 'About the Manual') + ',\n  ]},\n'
           + "  {group:'Manpower Planning and Selection', items:[\n"
           + item('ch2', '1', 'Dealership Organisation Structure', S['ch2']) + ',\n'
           + item('ch1', '2', 'Job Descriptions') + ',\n'
           + item('ch3', '3', 'Recruitment and Selection', S['ch3']) + ',\n'
           + item('ch4', '4', 'Compensation, Benefits and Incentive Policy', S['ch4']) + ',\n'
           + item('ch5', '5', 'Joining and Confirmation', S['ch5']) + ',\n  ]},\n'
           + "  {group:'Manpower Development', items:[\n"
           + item('ch6', '6', 'Learning and Development', S['ch6']) + ',\n'
           + item('ch7', '7', 'Performance Management', S['ch7']) + ',\n'
           + item('ch8', '8', 'Career Progression', S['ch8']) + ',\n'
           + item('ch9', '9', 'Employee Engagement, Rewards and Recognition', S['ch9']) + ',\n  ]},\n'
           + "  {group:'Manpower Governance', items:[\n"
           + item('ch10', '10', 'Discipline and Conduct', S['ch10']) + ',\n'
           + item('ch11', '11', 'Employee Exit Management', S['ch11']) + ',\n'
           + item('ch12', '12', 'Organisation Policies', S['ch12']) + ',\n  ]},\n'
           + "  {group:'ANNEXURE', items:[\n" + item('annexure', '', 'Annexures') + '\n  ]},\n];')
    a = h.find('window.JX_TOC = ['); b = h.find('];', a) + 2
    return h[:a] + toc + h[b:]


def _div_end(h, start):
    """index just after the </div> that closes the <div> opening at `start`."""
    depth, i = 0, start
    for m in re.finditer(r'<div\b|</div>', h[start:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            return start + m.end()
    raise ValueError('unbalanced')


def link_steps(h):
    """Lettered flow boxes jump to their step's heading; annexure chips jump to the annexure file."""
    art_re = re.compile(r'<article class="jx-chapter" id="chap-([^"]+)"')
    pieces, last, linked, miss = [], 0, 0, []
    for am in art_re.finditer(h):
        a, e = am.start(), h.find('</article>', am.end())
        if am.group(1) == 'annexure' or e < 0:
            continue
        seg, n = h[a:e], 0
        used, out, pos = set(), [], 0
        for fm in re.finditer(r'<div class="fx-flow"', seg):
            if fm.start() < pos:
                continue
            fend = _div_end(seg, fm.start())
            flow = seg[fm.start():fend]
            letters = re.findall(r'<span class="fx-badge">([A-Z])</span>', flow)
            if not letters or len(letters) != len(re.findall(r'<span class="fx-badge">', flow)):
                continue
            ids = {}
            for L in letters:
                hm = None
                for c in re.finditer(r'<h([456]) class="item-title([^"]*)"><span class="v7-mk">%s<span class="v7-mk-dot">\.</span></span>' % L, seg[fend:]):
                    if fend + c.start() not in used:
                        hm = c; break
                if not hm:
                    miss.append((am.group(1), L)); continue
                pos_h = fend + hm.start()
                used.add(pos_h)
                n += 1
                ids[L] = (pos_h, hm, f'{am.group(1)}-step-{n}')
            # rewrite headings (collected) and nodes
            new_flow, q = [], 0
            for nm in re.finditer(r'<div class="fx-node', flow):
                if nm.start() < q:
                    continue
                nend = _div_end(flow, nm.start())
                node = flow[nm.start():nend]
                L = re.search(r'<span class="fx-badge">([A-Z])</span>', node).group(1)
                if L in ids:
                    i0 = node.index('>') + 1
                    node = (node[:i0].replace('class="fx-node', 'class="fx-node fx-link', 1)
                            + '<a class="fx-go" href="#%s" aria-label="Go to step %s"></a>' % (ids[L][2], L) + node[i0:])
                new_flow.append(flow[q:nm.start()] + node); q = nend
            new_flow.append(flow[q:])
            out.append((fm.start(), fend, ''.join(new_flow)))
            pos = fend
            for L, (ph, hm, hid) in ids.items():
                out.append((ph, ph + len('<h%s class="item-title%s"' % (hm.group(1), hm.group(2))),
                            '<h%s id="%s" class="item-title%s"' % (hm.group(1), hid, hm.group(2))))
        res, q = [], 0
        for s0, s1, rep in sorted(out):
            res.append(seg[q:s0] + rep); q = s1
        res.append(seg[q:])
        pieces.append((a, e, ''.join(res)))
        linked += n
    for a, e, rep in reversed(pieces):
        h = h[:a] + rep + h[e:]
    # annexure chips -> the annexure file entry
    a = h.find('id="chap-annexure"'); e = h.find('</article>', a)
    seg = h[a:e]
    codes = set(re.findall(r'title="Download (\d{1,2}[A-Z])\. ', seg))
    seg = re.sub(r'(<a class="annex-file-item" href="#annexure")( onclick="handleAnnexDownload\(event, \'(\d{1,2}[A-Z])\.)',
                 lambda m: m.group(1).replace('<a ', '<a id="annex-%s" ' % m.group(3)) + m.group(2), seg)
    h = h[:a] + seg + h[e:]
    used_codes = set(re.findall(r'<span class="v7-ref">(\d{1,2}[A-Z])</span>', h))
    assert used_codes <= codes, used_codes - codes
    h = re.sub(r'<span class="v7-ref">(\d{1,2}[A-Z])</span>', r'<a class="v7-ref" href="#annex-\1">\1</a>', h)
    print('step links', linked, 'unmatched', miss)
    return h


CSS = '''<style id="jx-v7">
.jx-chapter h5.item-title{font-size:14.5px;font-weight:700;margin:18px 0 6px}
.jx-chapter h6.item-title{font-size:14px;font-weight:600;font-style:italic;margin:14px 0 4px;color:var(--grey-700,#444)}
.jx-chapter .zigzag-pill .zz-body{display:flex;flex-direction:column;min-width:0}
.jx-chapter .zigzag-pill .zz-when{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;opacity:.7;margin-bottom:2px}
.jx-chapter .zigzag-pill .zz-who{font-size:12px;font-style:italic;opacity:.75;margin-top:3px}
.jx-chapter .zigzag-pill.zz-rms{background:#FAE2D5;border-color:#E9B79B}
.jx-chapter .v7-img{margin:16px 0}
.jx-chapter .v7-img img{display:block;width:100%;height:auto !important;object-fit:contain !important;aspect-ratio:auto !important}
.jx-chapter blockquote.v7-quote{margin:16px 0;padding:14px 18px;border-left:3px solid var(--line-200,#ccc);font-style:italic}
.jx-chapter .v7-disclaimer{font-size:13px;opacity:.85}
.jx-chapter .rf-phase-badge{background:rgba(255,255,255,.16);color:#fff}
.jsw-diagram-canvas [style*="background:linear-gradient(145deg,#2c2c2c"] [style*="background:linear-gradient(145deg,#fdfdfd"] *,
.jsw-diagram-canvas [style*="background:linear-gradient(145deg,#2c2c2c"] [style*="background:linear-gradient(145deg,#fdfdfd"]{color:#0A0A0A !important}
.jx-chapter .rf-step-card.zz-rms{background:#FAE2D5;border-color:#E9B79B}
.jx-chapter .v7-cat{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;margin:2px 4px 2px 0;border:1px solid var(--line-200,#ccc)}
.jx-chapter .v7-cat-product{background:#E4E4E7}
.jx-chapter .v7-cat-process{background:#CFCFD4}
.jx-chapter .v7-cat-soft{background:#F2F2F4}
.jx-chapter .ch-month-notes{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0 10px}
.jx-chapter .ch-month-notes:empty{display:none}
.jx-chapter .ch-month-notes .ch-pill{cursor:pointer;font-size:11px;padding:4px 8px;white-space:normal}
.jx-chapter .ch-notes-label{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.6;margin-right:4px}
.jx-chapter .v7-phone{display:none}
@media (max-width:600px){.jx-chapter .v7-desk{display:none !important}.jx-chapter .v7-phone{display:block}}
.jx-hero-quote{margin:18px auto 0;font-style:italic;opacity:.8;text-align:center}

/* ── reading: hierarchy + emphasis (markup from readability.py; wording untouched) ── */
.jx-chapter section.chap{--rd-ink:#1d1d1f;--rd-body:#333336;--rd-mark:rgba(17,17,19,.11)}
.jx-chapter section.chap .prose p{color:var(--rd-body);font-size:16px;line-height:1.72;max-width:74ch}
.jx-chapter section.chap .prose .list-clean li{color:var(--rd-body);font-size:15.5px;line-height:1.7;max-width:76ch}
.jx-chapter section.chap .prose .list-clean li + li{margin-top:4px}
.jx-card-bar i{background:linear-gradient(90deg,#9A6B0A,#C5A059)}
.jx-chapter section.chap .prose > h4.item-title{font-size:19px;line-height:1.35;font-weight:750;letter-spacing:-.012em;color:var(--rd-ink);
  margin:44px 0 12px;padding-top:22px;border-top:1.5px solid rgba(17,17,19,.22);display:flex;align-items:flex-start;gap:12px;text-wrap:balance}
.jx-chapter section.chap .prose > hr,.jx-chapter hr{border:none;border-top:1.5px solid rgba(17,17,19,.22);margin:36px 0}
.jx-chapter section.chap .prose > h3 + h4.item-title,.jx-chapter section.chap .prose > h4.item-title:first-child{border-top:0;padding-top:0;margin-top:20px}
.jx-chapter section.chap .prose > h5.item-title{font-size:16.5px;line-height:1.4;font-weight:720;color:var(--rd-ink);margin:30px 0 8px;letter-spacing:-.005em}
.jx-chapter section.chap .prose > h6.item-title{font-size:15.5px;line-height:1.4;font-weight:700;font-style:normal;color:var(--rd-ink);margin:26px 0 8px;display:flex;align-items:center;gap:10px}
.jx-chapter .v7-mk{flex:none;display:inline-grid;place-items:center;min-width:28px;height:28px;padding:0 7px;border-radius:8px;background:var(--ink);color:#fff;
  font-size:13px;font-weight:750;letter-spacing:0;font-variant-numeric:tabular-nums;margin-top:-1px}
.jx-chapter .v7-mk.v7-mk-lower{min-width:0;height:auto;padding:0;border-radius:0;background:none;color:var(--rd-ink,#1d1d1f);font-size:inherit;font-weight:600;margin:0 -4px 0 0}
.jx-chapter .v7-mk-dot{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.jx-chapter section.chap .prose p.v7-runin{font-size:17.5px;line-height:1.4;color:var(--rd-ink);margin:34px 0 10px;letter-spacing:-.01em}
.jx-chapter section.chap .prose p.v7-runin strong{font-weight:750}
.jx-chapter strong.v7-lead{color:var(--rd-ink,#1d1d1f);font-weight:700}
.jx-chapter .v7-key{color:var(--rd-ink,#1d1d1f);font-weight:650;font-variant-numeric:tabular-nums;white-space:nowrap;
  background:linear-gradient(transparent 58%,var(--rd-mark,rgba(17,17,19,.11)) 58%,var(--rd-mark,rgba(17,17,19,.11)) 92%,transparent 92%);padding:0 1px}
.jx-chapter .v7-ref{display:inline-block;font-style:normal;font-weight:700;font-size:.82em;line-height:1.45;letter-spacing:.02em;color:var(--ink);
  padding:0 6px;border:1px solid var(--line-200);border-radius:5px;background:#fff;vertical-align:.08em;white-space:nowrap}
.jx-chapter .v7-chart-cap{display:flex;flex-wrap:wrap;gap:6px 18px;margin:14px 0 6px;font-size:13.5px;font-weight:650;color:var(--rd-ink,#1d1d1f)}
.jx-chapter .v7-chart-cap:empty{display:none}

</style>
'''


def inject_css(h):
    assert 'id="jx-v7"' not in h
    css = CSS.replace('</style>', (Path(__file__).with_name('flow.css')).read_text() + '</style>')
    return h.replace('</head>', css + '</head>', 1)


if __name__ == '__main__':
    build()
