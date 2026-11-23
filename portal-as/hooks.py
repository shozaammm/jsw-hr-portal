"""Renderer hooks for the Service manual: shapes, pictures and lists that become infographics.
Every visible word is from the docx (paragraphs, tables, shape text, or the text printed in its pictures)."""
import html, re, subprocess
import asdoc  # noqa
import build as B
import flowcharts as fc
import infographics as G

esc = lambda s: html.escape(s, quote=False)

# ── hashes of the docx pictures ──
IMG_INDUCTION = 'b28a6280'
IMG_TMS = '6da07e08'
IMG_ENQUIRY = '48556eb9'

# transcribed from the pictures
TMS_FLOW = ('Training Process Flow in TMS for JSW Trainings', [
    ('Training Calendar Release', 'JSW Motors releases monthly training calendar & nominates dealer manpower'),
    ('Nomination Confirmation', 'Nomination available on TMS to respective IDT for review & confirmation'),
    ('Attend Scheduled Training', 'Confirmed manpower attends scheduled training at venue'),
    ('Attendance Capture', 'Attendance marked digitally in TMS by the trainee'),
    ('Pre & Post Training Assessment', 'Pre & Post training assessment conducted digitally through the TMS'),
    ('Results Published & Visibility', 'Assessment results generated & published in real-time, immediate visibility for Trainers & Dealers'),
])
ENQUIRY = ('Employee Enquiry Process', [
    ('Appoint Enquiry Officer', 'Neutral; not involved in the case and not the complainant.'),
    ('Issue Written Notice', 'Date, time and venue communicated to the employee at least three days in advance.'),
    ('Confirm Representation', 'A colleague may accompany the employee. External legal representation is not permitted.'),
    ('Provide Case Materials', 'Employee is given access to all documents and evidence being considered in the case.'),
    ('Record Witness Statements', 'Witnesses provide statements, and the employee has an opportunity to ask questions.'),
    ('Employee Presents Their Case', 'Employee may present an explanation and provide supporting evidence or witnesses.'),
    ('Maintain Written Record', 'Proceedings are recorded in writing and signed by the relevant parties.'),
    ('Enquiry Officer Records Findings', 'Findings and reasons are recorded based on the evidence presented.'),
    ('Final Decision', 'Dealer Principal decides the final disciplinary action, if any.'),
])
INDUCTION = {
    'title': 'Employee Induction', 'sub': 'HR department monitors · IDT conducts the sessions',
    'cols': [
        ('HR Induction', 'HR Manager', 'Joining day', [
            ('Joining handover', ['Welcome letter and joining kit', 'Workstation and system access', 'PF transfer form, if applicable']),
            ('Ground rules', ['Operational hours and salary date', 'Marking attendance, applying for leave']),
            ('Code of conduct', ['Business ethics and expected conduct'])]),
        ('General Induction', 'HR Manager with IDT', 'Days 1–2', [
            ('Overview', ['History and organisation chart', 'Vision, mission and values', 'Quality policy', 'Business objectives and performance']),
            ('Working hours', ['Shift timings and breaks', 'Recording attendance and late coming']),
            ('Pay and benefits', ['Pay period and payment mode', 'Group insurance', 'ESIC and PF compliance']),
            ('Personnel policies', ['Employee classification', 'Employment administration', 'Working and living conditions',
                                    'Probation and confirmation', 'Performance appraisal', 'Discipline and grievance redressal']),
            ('Leave', ['Leave types, holidays and entitlement', 'Approvals, LWP and encashment'])]),
        ('Department Induction', 'Reporting Manager with IDT', 'Days 2–7', [
            ('Overview', ['Department goals and alignment', 'Department structure', 'Internal working systems']),
            ('Role clarity', ['Roles and responsibilities', 'Reporting structure', 'Coordination with other departments',
                              'Technical or functional aspects', 'Career progression opportunities']),
            ('Expectation clarity', ['Individual performance criteria (KPIs)', 'Behavioural expectations']),
            ('Training and development', ['On-the-job training calendar', 'Buddy support (see 5.1.7)'])]),
    ]}

DOT = {'6FA8F0': 'Product', 'F79B42': 'Process', '77933C': 'Soft Skills'}


def induction_tree():
    d = INDUCTION
    cols = ''
    for i, (name, who, when, boxes) in enumerate(d['cols'], 1):
        bx = ''.join(f'<div class="as-ind-box"><h5>{esc(h)}</h5><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul></div>' for h, items in boxes)
        cols += (f'<div class="as-ind-col"><div class="as-ind-head"><span class="as-ind-n">{i}</span><h4>{esc(name)}</h4>'
                 f'<em>{esc(who)}</em><b>{esc(when)}</b></div>{bx}</div>')
    return (f'<figure class="as-ind"><div class="as-ind-root"><h4>{esc(d["title"])}</h4><p>{esc(d["sub"])}</p></div>'
            f'<div class="as-ind-cols">{cols}</div></figure>')


# ───────────────────────── shape groups ─────────────────────────
def sh_text(sp):
    return ' '.join(sp['paras'])


def level_cards(grp, title_rows):
    """Learner-journey groups: (title, subtitle) header shapes + (level head, body) pairs + link labels."""
    return None


def parse_journey(grp):
    """Group of shapes -> list of cards {title, subtitle, steps[(head, [lines])], links[labels], end}."""
    heads = [s for s in grp if s['prst'] == 'rect' and s['h'] == 18 and s['paras'] and s['x'] == 0]
    subs = [s for s in grp if s['prst'] == 'rect' and s['h'] == 14 and s['paras']]
    bodies = [s for s in grp if s['prst'] == 'roundRect']
    tabs = [s for s in grp if s['prst'] == 'round2SameRect']
    links = [s for s in grp if s['prst'] == 'rect' and s['paras'] and s['h'] in (34,) and s['w'] in (46, 60)]
    cards = []
    for hd in heads:
        sub = next(s for s in subs if abs(s['y'] - (hd['y'] + hd['h'])) < 3)
        band = [b for b in bodies if hd['y'] + 30 < b['y'] < hd['y'] + 50]
        band.sort(key=lambda s: s['x'])
        steps = []
        for b in band:
            t = next(t for t in tabs if t['x'] == b['x'] and abs(t['y'] - b['y']) < 3)
            steps.append((' '.join(t['paras']), b['paras']))
        lk = sorted([l for l in links if hd['y'] + 28 < l['y'] < hd['y'] + 80], key=lambda s: s['x'])
        cards.append({'title': ' '.join(hd['paras']), 'subtitle': ' '.join(sub['paras']), 'steps': steps,
                      'links': [' '.join(l['paras']) for l in lk]})
    cards.sort(key=lambda c: 0)
    return cards


def journey_html(cards):
    out = []
    for c in cards:
        steps, links = c['steps'], c['links']
        track = []
        for i, (head, lines) in enumerate(steps):
            body = '<br>'.join(esc(x) for x in lines)
            track.append(f'<div class="fx-lj-step"><div class="fx-lj-head">{esc(head)}</div><div class="fx-lj-body">{body}</div></div>')
            if i < len(steps) - 1:
                lab = links[i] if i < len(links) else ''
                track.append(f'<div class="fx-lj-link"><span class="fx-lj-label">{esc(lab)}</span><span class="fx-arrow"></span></div>')
        if len(links) == len(steps):
            track.append(f'<div class="fx-lj-link fx-lj-end"><span class="fx-lj-label">{esc(links[-1])}</span>{fc.TROPHY}</div>')
        out.append(f'<section class="fx-lj-card"><h4 class="fx-lj-title">{esc(c["title"])}</h4><p class="fx-lj-sub">{esc(c["subtitle"])}</p>'
                   f'<div class="fx-lj-track">' + ''.join(track) + '</div></section>')
    return '<div class="fx-lj">' + ''.join(out) + '</div>'


def tna_html(grp):
    title = next(s for s in grp if s['paras'] and s['paras'][0] == 'TNA Process')
    hdr = sorted([s for s in grp if s['fill'] == '1B2A3D'], key=lambda s: s['x'])
    head = [s['paras'][0].title() if s['paras'][0].isupper() else s['paras'][0] for s in hdr]
    rows = []
    texts = sorted([s for s in grp if s['paras'] and s['x'] == 0 and s['y'] > 40 and s['w'] == 110], key=lambda s: s['y'])
    for r in texts:
        m = next(s for s in grp if s['x'] == 110 and s['y'] == r['y'] and s['paras'])
        cats = [DOT[s['fill']] for s in sorted(grp, key=lambda s: s['x']) if s['prst'] == 'ellipse' and r['y'] < s['y'] < r['y'] + 27 and s['fill'] in DOT]
        rows.append((r['paras'][0], ' '.join(m['paras']), cats))
    return B.__dict__['tna_table_html'](title['paras'][0], head, rows) if False else G_tna(title['paras'][0], head, rows)


def G_tna(title, head, rows):
    cats = {'Product': 'v7-cat-product', 'Process': 'v7-cat-process', 'Soft Skills': 'v7-cat-soft'}
    body = ''.join(f'<tr><td><strong>{esc(p)}</strong></td><td>{esc(m)}</td><td>'
                   + ''.join(f'<span class="v7-cat {cats[c]}">{esc(c)}</span>' for c in cs) + '</td></tr>' for p, m, cs in rows)
    return (f'<h5 class="item-title v7-h5">{esc(title)}</h5><div class="table-wrap"><table><thead><tr>'
            + ''.join(f'<th>{esc(h)}</th>' for h in head) + f'</tr></thead><tbody>{body}</tbody></table></div>')


def calendar_cards(grp):
    banner = next(s for s in grp if s['fill'] == '1F3864' and s['y'] == 0)
    heads = [s for s in grp if s['prst'] == 'round2SameRect']
    bodies = [s for s in grp if s['prst'] == 'roundRect' and s['fill'] == 'F2F2F2']
    cards = []
    for h in heads:
        b = next(b for b in bodies if b['x'] == h['x'] and abs(b['y'] - h['y']) < 3)
        cards.append((h['x'], h['y'], ' '.join(h['paras']), [re.sub(r'^•\s*', '', p) for p in b['paras']]))
    # snake order = the CARD_POS used by the portal: row-major top row L→R, middle row R→L, bottom row L→R
    rows = sorted({c[1] for c in cards})
    ordered = []
    for ri, y in enumerate(rows):
        rc = sorted([c for c in cards if c[1] == y], key=lambda c: c[0])
        ordered += rc if ri % 2 == 0 else rc[::-1]
    return banner['paras'][0], [(t, b) for _, _, t, b in ordered]


def sample_plan(grp):
    weeks = sorted([s for s in grp if s['paras'] and s['paras'][0].startswith('Week ')], key=lambda s: s['x'])
    cap = next(s for s in grp if s['paras'] and s['paras'][0] == 'SAMPLE WEEK-WISE TRAINING PLAN')
    note = next(s for s in grp if s['paras'] and s['paras'][0].startswith('TNA (N Month)'))
    cards = ''.join(
        f'<li class="fx-chev-step" style="--c:{fc.SEQ[(i + 1) % len(fc.SEQ)]}"><div class="fx-chev-head"><span class="fx-chev-n">{i + 1}</span>{esc(w["paras"][0])} — {esc(w["paras"][1])}</div>'
        f'<p class="fx-text">{esc(w["paras"][2])}</p></li>' for i, w in enumerate(weeks))
    return (f'<h5 class="item-title v7-h5">{esc(cap["paras"][0].capitalize())}</h5><figure class="fx-fig"><ol class="fx-chev">{cards}</ol></figure>'
            f'<p class="as-note"><strong>{esc(note["paras"][0].split(" | ")[0])}</strong> | {esc(" | ".join(note["paras"][0].split(" | ")[1:]))}</p>')


def cycle_html(grp):
    steps = [s for s in grp if s['prst'] == 'ellipse' and s['paras'] and s['paras'][0].startswith('STEP')]
    centre = next(s for s in grp if s['paras'] and s['paras'][0] == 'PERFORMANCE')
    steps.sort(key=lambda s: int(s['paras'][0].split()[1]))
    items = [(s['paras'][1], ' · '.join(s['paras'][2:])) for s in steps]
    return fc.chevrons(items), ' '.join(centre['paras'])


def shape_html(R, b):
    out = []
    for grp in b['groups']:
        txt = ' '.join(sh_text(s) for s in grp)
        if txt.startswith('Customer-facing roles') or txt.startswith('Technical roles'):
            out.append(journey_html(parse_journey(grp)))
        elif txt.startswith('TNA Process'):
            out.append(tna_html(grp))
        elif 'Training Calendar Finalisation Process' in txt:
            title, cards = calendar_cards(grp)
            out.append(fc.module_snake(title, [(t, bl) for t, bl in cards]) + sample_plan(grp))
        elif 'PERFORMANCE' in txt and 'STEP 1' in txt:
            h, centre = cycle_html(grp)
            out.append(f'<h5 class="item-title v7-h5">{esc(centre.title())}</h5>' + h)
        else:
            assert txt.strip() in ('', '6 to 8 years'), txt[:80]        # arrows / a stray note in the docx
    return ''.join(out)


# ───────────────────────── normalisation of the docx openers ─────────────────────────
PUA = re.compile(r'^[-•·]\s*')
GLUE = re.compile(r'^:?\s*(Objective)\s*:?\s*(.*\S)$', re.S)


def clone(b, text):
    nb = dict(b)
    nb['text'] = text.strip(); nb['html'] = esc(text.strip())
    return nb


def normalize(blocks):
    out, in_open = [], True
    bullet = {'ilvl': 0, 'fmt': 'bullet', 'marker': ''}
    lab = False
    for b in blocks:
        if b['k'] == 'p' and b['lvl'] == 2:
            in_open = False
        if b['k'] != 'p' or not in_open or b['lvl']:
            out.append(b); continue
        t = PUA.sub('', b['text'])
        m = GLUE.match(t)
        if m and not b['num'] or (m and m.group(2) and m.group(1) == 'Objective'):
            label = clone(b, 'Objective'); label['num'] = None
            out.append(label)
            item = clone(b, m.group(2)); item['num'] = b['num'] or bullet
            out.append(item); lab = True
            continue
        if re.match(r'^:?\s*(Objective|Purpose|Principles|Benefits? (for|to))', t) and t.endswith(':') or t in (':', ':  Objective'):
            nb = clone(b, 'Objective' if 'Objective' in t else t.rstrip(':')); nb['num'] = None
            out.append(nb); lab = True; continue
        if lab and not b['num'] and b['style'] not in ('Intense Quote',) and len(t) < 150 and not t.endswith(':') \
                and not t.startswith(('In this chapter', 'This chapter', 'The joining', 'Performance management is')):
            nb = clone(b, t); nb['num'] = bullet; out.append(nb); continue
        if t != b['text']:
            nb = clone(b, t); nb['num'] = b['num']; out.append(nb); continue
        out.append(b)
    return out


# ───────────────────────── hooks ─────────────────────────
def lms_steps(items):
    steps = []
    for t in items:
        name, _, rest = t.partition(' - ')
        steps.append((name.strip(), rest.strip()))
    return steps


def make(T, ctx):
    chunks = ctx['chunks']
    head = subprocess.run(['git', 'show', 'HEAD:v2.html'], cwd=asdoc.HERE.parent, capture_output=True, text=True, check=True).stdout
    a = head.find('id="chap-ch6"'); a = head.find('<!--ld-orig', a); a = head.find('-->', a) + 3
    LD = head[a:B._div_end(head, head.find('<div class="ig-ldm"', a))]
    texts_after = lambda bl, i, n: [bl[i + 1 + k]['text'] for k in range(n)]
    state = {'learning': False}

    def hook(R, bl, i):
        b = bl[i]; cid = R.cid
        if b['k'] == 'shape':
            return shape_html(R, b), 1
        if b['k'] == 'tbl':
            if not any(c.text.strip() for r in b['t'].rows for c in r.cells):
                return '', 1
            first = b['t'].rows[0].cells[0].text.strip()
            if cid == 'ch5' and first in ('KEY COMPONENTS OF EMPLOYEE INDUCTION',):
                return '', 1
            if cid == 'ch5' and first == 'Overview' and len(b['t'].rows) == 2 and len(B.cells_of(b['t'].rows[0])) == 4:
                return '', 1
            if cid == 'ch8' and first == 'Work Area':
                rows = [[c.text.strip() for c in B.cells_of(r)] for r in b['t'].rows]
                nxt = bl[i + 1]['text'] if i + 1 < len(bl) else ''
                cap, _, note = nxt.partition('\n')
                assert cap.startswith('Chart 8.1'), cap
                return G.career_matrix(T, rows, cap.strip()) + (f'\n<p>{esc(note.strip())}</p>' if note.strip() else ''), 2
            if cid == 'ch9' and first == 'Month':
                import calendar_as
                return calendar_as.build(T, ctx, b), 1
            return None
        t = b['text']
        if b['imgs']:
            h = b['imgs'][0][3]
            if h == IMG_INDUCTION: return induction_tree(), 1
            if h == IMG_TMS: return fc.vlist(*TMS_FLOW), 1
            if h == IMG_ENQUIRY: return fc.vlist(*ENQUIRY), 1
            return None
        if cid == 'ch6' and t.startswith('Learning design should be scientifically driven'):
            n = 0
            while bl[i + 1 + n]['num']: n += 1
            assert n == 5, n
            return f'<p>{b["html"]}</p>' + LD, 1 + n
        if cid == 'ch6' and t.startswith('The LMS learning path comprises'):
            n = 0
            while bl[i + 1 + n]['num']: n += 1
            assert n == 5, n
            return f'<p>{b["html"]}</p>' + fc.chevrons(lms_steps(texts_after(bl, i, 5))), 1 + n
        if cid == 'ch6' and t == 'i. Training delivery coverage':
            a2 = texts_after(bl, i, 2); b2 = bl[i + 3]
            assert b2['text'] == 'ii. Effectiveness'
            c = texts_after(bl, i + 3, 2)
            return fc.ring(['What IDT', 'reports'], [(t, a2), (b2['text'], c)]), 6
        if cid == 'ch7' and t == 'Follow the SMART framework while setting KPIs:':
            rows = []
            for x in texts_after(bl, i, 5):
                l, w, d = [p.strip() for p in re.split(r'\s+–\s+', x, maxsplit=2)]
                rows.append((l, w, d))
            return f'<p>{b["html"]}</p>' + fc.smart(rows), 6
        if cid == 'ch7' and t == 'Review performance expectations against the set KPIs:':
            return f'<p>{b["html"]}</p>' + fc.review(texts_after(bl, i, 4)), 5
        if cid == 'ch9' and t.startswith('Managers should immediately recognise'):
            return f'<p>{b["html"]}</p>' + fc.spot(texts_after(bl, i, 3), 'SPOT'), 4
        return None
    return hook
