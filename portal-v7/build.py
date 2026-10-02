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
import base64, hashlib, html, io, re, subprocess, sys
from pathlib import Path

import docx
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


def table_html(t, D):
    rows = [cells_of(r) for r in t.rows]
    rows = [r for r in rows if any(c.text.strip() for c in r)]
    if not rows:
        return ''
    ncol = max(len(r) for r in rows)
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
                    while i + 1 < len(blocks) and blocks[i + 1]['k'] == 'tbl' and is_flow(blocks[i + 1]['t']):
                        i += 1; group.append(blocks[i]['t'])
                    self.out.append(flow_html(group))
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
    ('TNA Report (Input)', ['Inputs for: Product, Process & Soft Skills Trainings', 'Avoid – assuming needs without data & Validation',
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
    ('Feedback Collection', ['Take participant feedback using feedback form 6B', 'Avoid – Not evaluating feedback and taking corrective action',
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
            if cid == 'ch3' and is_flow(b['t']):
                steps = [(n, ' '.join(body), (when + who) or [], rms) for n, when, body, who, rms in flow_cells([b['t']])]
                return G.rf_flow(T, steps), 1
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
            if h == IMG_LEARNER_JOURNEY: return G.learner_journey(T, LEARNER_JOURNEY) + tail, 1
            if h == IMG_TMS_FLOW: return G.step_flow(T, TMS_FLOW[1], TMS_FLOW[0]) + tail, 1
            if h == IMG_TNA_TABLE: return tna_table_html(*TNA_TABLE) + tail, 1
            if h == IMG_CAL_FINAL: return G.module_cards(T, *CAL_FINAL) + tail, 1
            if h == IMG_SAMPLE_PLAN: return plan_table_html(*SAMPLE_PLAN) + tail, 1
            if h == IMG_LMS: return phone_fallback(G.chevrons(T, LMS_STEPS), [f'<strong>{esc(a)}</strong> – {esc(b)}' for a, b in LMS_STEPS]) + tail, 1
            return None
        if cid == 'ch4' and t.startswith('Interest free salary advance'):
            items = texts_after(blocks, i, 4)
            return f'<p>{b["html"]}</p>' + phone_fallback(G.cycle4(T, items, ['Salary', 'advance']), [esc(x) for x in items]), 5
        if cid == 'ch6' and t == 'i. Training delivery coverage':
            a, b2 = texts_after(blocks, i, 2), blocks[i + 3]
            assert b2['text'] == 'ii. Effectiveness'
            c = texts_after(blocks, i + 3, 2)
            return phone_fallback(G.ring(T, ['What IDT', 'reports'], [(t, a), (b2['text'], c)]), [f'<strong>{esc(t)}</strong><ul class="list-clean">' + ''.join(f'<li>{esc(x)}</li>' for x in a) + '</ul>', f'<strong>{esc(b2["text"])}</strong><ul class="list-clean">' + ''.join(f'<li>{esc(x)}</li>' for x in c) + '</ul>']), 6
        if cid == 'ch7' and t == 'Follow the SMART framework while setting KPIs:':
            rows = []
            for x in texts_after(blocks, i, 5):
                l, w, d = [p.strip() for p in re.split(r'\s+–\s+', x, maxsplit=2)]
                rows.append((l, w, d))
            return f'<p>{b["html"]}</p>' + G.smart(T, rows), 6
        if cid == 'ch7' and t == 'Review performance expectations against the set KPIs:':
            return f'<p>{b["html"]}</p>' + G.review_cards(T, texts_after(blocks, i, 4)), 5
        if cid == 'ch9' and t.startswith('Managers should immediately recognise'):
            return f'<p>{b["html"]}</p>' + phone_fallback(G.spot(T, texts_after(blocks, i, 3), 'SPOT'), [esc(x) for x in texts_after(blocks, i, 3)]), 4
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
    about = about.replace('<p>Introduction to Unified Apps</p>', '<h3 class="sub-title subhead">Introduction to Unified Apps</h3>')
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

    # chapters 3-12 were locked (fb2dafc) until their content matched the new manual; V7 content is now in
    lock = "['i', 'ii', 'iii', '1', '2'].indexOf(ch.num) === -1"
    assert html_out.count(lock) == 2
    html_out = html_out.replace(lock, 'false')
    for guard in ("""    if(res && res.page && res.page.ch){
      if(['i', 'ii', 'iii', '1', '2'].indexOf(res.page.ch.num) === -1){
        return null; // Locked chapter routes back to home
      }
    }
""", """    if(res.next && res.next.ch && ['i', 'ii', 'iii', '1', '2'].indexOf(res.next.ch.num) === -1){
      res.next = null;
    }
"""):
        assert html_out.count(guard) == 1
        html_out = html_out.replace(guard, '')
    assert "['i', 'ii', 'iii', '1', '2']" not in html_out
    # groups lost their "Part X · " prefix (ab1bffd), so short === name and the sidebar printed it twice
    dup = "g.name ? '<b>' + esc(g.short) + '</b><span>' + esc(g.name) + '</span>'"
    assert html_out.count(dup) == 1
    html_out = html_out.replace(dup, "g.name && g.name !== g.short ? '<b>' + esc(g.short) + '</b><span>' + esc(g.name) + '</span>'")
    html_out = patch_home(html_out)
    html_out = patch_toc(html_out, toc_subs)
    html_out = inject_css(html_out)
    OUT.write_text(html_out)
    print('wrote', OUT, len(html_out))


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
.jx-chapter .v7-cat-product{background:#DCE8F7}
.jx-chapter .v7-cat-process{background:#FBE3CC}
.jx-chapter .v7-cat-soft{background:#E1EBD3}
.jx-chapter .ch-month-notes{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0 10px}
.jx-chapter .ch-month-notes:empty{display:none}
.jx-chapter .ch-month-notes .ch-pill{cursor:pointer;font-size:11px;padding:4px 8px;white-space:normal}
.jx-chapter .ch-notes-label{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.6;margin-right:4px}
.jx-chapter .v7-phone{display:none}
@media (max-width:600px){.jx-chapter .v7-desk{display:none !important}.jx-chapter .v7-phone{display:block}}
.jx-hero-quote{margin:18px auto 0;font-style:italic;opacity:.8;text-align:center}
</style>
'''


def inject_css(h):
    assert 'id="jx-v7"' not in h
    return h.replace('</head>', CSS + '</head>', 1)


if __name__ == '__main__':
    build()
