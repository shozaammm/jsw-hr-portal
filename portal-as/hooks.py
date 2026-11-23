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
            body = f'<strong class="as-lj-when">{esc(lines[0])}</strong>' + ''.join(f'<span class="as-lj-obj">{esc(x)}</span>' for x in lines[1:])
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
        f'<li class="fx-chev-step" style="--c:{fc.SEQ[(i + 1) % len(fc.SEQ)]}"><div class="fx-chev-head"><span class="fx-chev-n">{i + 1}</span>{esc(w["paras"][0])}</div><p class="as-theme">{esc(w["paras"][1])}</p>'
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
        if t.strip() in (':', ''):
            continue
        m = GLUE.match(t)
        if m:
            g2 = (m.group(2) or '').strip()
            if g2 in (':', ''):
                label = clone(b, 'Objective'); label['num'] = None
                out.append(label); lab = True
                continue
            if not b['num'] or (m.group(1) == 'Objective'):
                label = clone(b, 'Objective'); label['num'] = None
                out.append(label)
                item = clone(b, g2); item['num'] = b['num'] or bullet
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


def talent_grid(t):
    rows = [[c.text.strip() for c in B.cells_of(r)] for r in t.rows]
    head = rows[0]
    tone = {('High', 2): 3, ('High', 3): 2, ('Medium', 3): 2}
    body = ''
    for r in rows[1:]:
        cells = ''
        for j, x in enumerate(r[1:], 1):
            lvl = {'High': 2, 'Medium': 1, 'Low': 0}[r[0]] + {1: 0, 2: 1, 3: 2}[j]
            cells += f'<td class="as-tg-c as-tg-{lvl}">{esc(x)}</td>'
        body += f'<tr><th scope="row" class="as-tg-r">{esc(r[0])}</th>{cells}</tr>'
    ths = ''.join(f'<th>{esc(h)}</th>' for h in head[1:])
    return (f'<div class="table-wrap as-tg"><table><thead><tr><th class="as-tg-corner">{esc(head[0])}</th>{ths}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def attrition_card(bl, i):
    t = bl[i]['text']
    f, _, note = t.partition('\n')
    if not note:
        m = re.match(r'^(.*?x 100)\s*(Note:.*)$', t, re.S)
        f, note = (m.group(1), m.group(2)) if m else (t, '')
    k = i + 1
    assert bl[k]['text'].startswith('Example:')
    lines = [bl[k + j]['text'] for j in range(1, 5)]
    eq = ''
    out = (f'<div class="as-attr"><div class="as-attr-f"><span>Manpower Attrition</span><b>=</b><span>Manpower Left / (Manpower Opening + Manpower Joined) x 100</span></div>'
           + (f'<p class="as-attr-n">{esc(note.strip())}</p>' if note.strip() else '')
           + f'<div class="as-attr-e"><h5>{esc(bl[k]["text"])}</h5><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in lines[:3])
           + f'<li class="as-attr-r">{esc(lines[3])}</li></ul></div></div>')
    return out, 6


def smart_kpi_card():
    return '''<div class="as-smart-card reveal">
  <div class="as-goal-block as-goal-dealership">
    <div class="as-goal-header">
      <div class="as-goal-badge">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M3 7v14M21 7v14M6 7V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v3M9 10h2M13 10h2M9 14h2M13 14h2M9 18h2M13 18h2"/></svg>
        <span>Dealership Goal</span>
      </div>
    </div>
    <div class="as-goal-text">
      Monthly Workshop Throughput = 1,200 repair orders (with 8 Service Advisors) | CSI score of &gt; 95% | Labour revenue of ₹18 lakh and parts revenue of ₹30 lakh per month (assumed average of ₹1,500 labour and ₹2,500 parts per repair order) (this is derived from the Annual Aftersales Business Plan of the dealership)
    </div>
  </div>

  <div class="as-goal-cascade">
    <div class="as-cascade-pill">
      <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
      <span>Service Advisor KPI</span>
    </div>
  </div>

  <div class="as-goal-block as-goal-sa">
    <div class="as-goal-header">
      <div class="as-goal-badge as-badge-role">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="7" r="4"/><path d="M5.5 21a6.5 6.5 0 0 1 13 0"/></svg>
        <span>Service Advisor KPI</span>
      </div>
    </div>
    <div class="as-goal-text">
      Handle an average of 450 repair orders per quarter per SA in the financial year | CSI score of 95% for all customers handled in the month | Generate labour revenue of ₹6.75 lakh and parts revenue of ₹11.25 lakh per quarter
    </div>
  </div>

  <div class="as-smart-breakdown">
    <div class="as-smart-heading">
      <span class="as-smart-title">How is it SMART</span>
    </div>
    <div class="as-smart-grid">
      <div class="as-smart-item">
        <div class="as-smart-letter">S</div>
        <div class="as-smart-content">
          <div class="as-smart-name">Specific</div>
          <p class="as-smart-text">Average 450 repair orders per quarter, with ₹1,500 labour and ₹2,500 parts revenue per repair order | CSI score of 95%</p>
        </div>
      </div>
      <div class="as-smart-item">
        <div class="as-smart-letter">M</div>
        <div class="as-smart-content">
          <div class="as-smart-name">Measurable</div>
          <p class="as-smart-text">150 repair orders per month (quarterly repair orders / 3), tracked in the DMS | Labour revenue of ₹2.25 lakh and parts revenue of ₹3.75 lakh per month (monthly repair orders × average labour and parts value per repair order), measured through DMS invoicing | Measurable through the CSI survey and post-service follow-up (PSF) feedback</p>
        </div>
      </div>
      <div class="as-smart-item">
        <div class="as-smart-letter">A</div>
        <div class="as-smart-content">
          <div class="as-smart-name">Achievable</div>
          <p class="as-smart-text">The goal is realistically achievable</p>
        </div>
      </div>
      <div class="as-smart-item">
        <div class="as-smart-letter">R</div>
        <div class="as-smart-content">
          <div class="as-smart-name">Relevant</div>
          <p class="as-smart-text">Repair order volume, labour and parts revenue, and CSI score are all relevant for the role of Service Advisor</p>
        </div>
      </div>
      <div class="as-smart-item">
        <div class="as-smart-letter">T</div>
        <div class="as-smart-content">
          <div class="as-smart-name">Time-bound</div>
          <p class="as-smart-text">Per quarter target, measured every quarter and reviewed at Annual Cycle</p>
        </div>
      </div>
    </div>
  </div>
</div>'''


def sample_email_card():
    return '''<div class="as-email-card reveal">
  <div class="as-email-window-bar">
    <span class="as-win-dot as-win-red"></span>
    <span class="as-win-dot as-win-yel"></span>
    <span class="as-win-dot as-win-grn"></span>
    <span class="as-win-title">Sample email</span>
  </div>
  <div class="as-email-headers">
    <div class="as-email-hdr-row"><span class="as-hdr-lbl">From:</span><span class="as-hdr-val">[Reporting Manager Email Address]</span></div>
    <div class="as-email-hdr-row"><span class="as-hdr-lbl">To:</span><span class="as-hdr-val">[Employee Email Address]</span></div>
    <div class="as-email-hdr-row"><span class="as-hdr-lbl">Cc:</span><span class="as-hdr-val">[HR Manager Email Address]</span></div>
    <div class="as-email-hdr-row"><span class="as-hdr-lbl">Subject:</span><span class="as-hdr-val"><strong>Quarterly/Mid-year Performance Review Summary</strong></span></div>
  </div>
  <div class="as-email-body">
    <p>Hi [Employee First Name],</p>
    <p>Thank you for sitting down with me today for your quarterly performance review. As discussed, this email summarises our meeting to ensure we are fully aligned moving forward.</p>
    
    <div class="as-email-section-title">a. Favourable results</div>
    <p>Your hard work reflected in several areas this quarter:</p>
    <ul class="list-clean" style="margin-left: 12px; margin-bottom: 12px;">
      <li>CSI score of 96% against a target of 95%</li>
      <li>Labour revenue of ₹1,650 per repair order against a target of ₹1,500</li>
      <li>No repeat repairs on the jobs you handled</li>
    </ul>

    <div class="as-email-section-title">b. Performance issues</div>
    <p>You finished the quarter averaging 110 repair orders per month, while our standard is a minimum of 150 repair orders per month.</p>

    <div class="as-email-section-title">c. Solution</div>
    <p>We have committed to the following action plan over the next 30 days:</p>
    <ul class="list-clean" style="margin-left: 12px; margin-bottom: 12px;">
      <li>Complete a 100% vehicle walk-around with a complete job card at reception for every vehicle</li>
      <li>Attend the IDT’s roleplay sessions on vehicle reception and estimate explanation every week</li>
    </ul>

    <p>We will review your repair orders, labour and parts revenue and job card quality in the DMS every Friday to track your progress and ensure you have the support you need to hit these numbers.</p>
    <p>I have great confidence in your ability to hit these targets, and I am fully committed to helping you succeed. Please reply directly to this email to confirm that this accurately reflects our conversation and your commitment to the plan.</p>
    <p style="margin-top: 18px; margin-bottom: 0;">Best regards,<br><strong>[Your Name]</strong><br>Service Manager<br>[Dealership Name]</p>
  </div>
</div>'''


def perks_card():
    return '''<div class="as-perks-container reveal">
  <div class="as-perks-header">
    <div class="as-perks-badge">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/><path d="M4 6v12a2 2 0 0 0 2 2h14v-4"/><circle cx="18" cy="12" r="2"/></svg>
      <span>Perks</span>
    </div>
  </div>
  <div class="as-perks-grid">
    <div class="as-perk-item">
      <div class="as-perk-icon">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
      </div>
      <div class="as-perk-text">
        <strong>Mobile allowance</strong>
      </div>
    </div>
    <div class="as-perk-item">
      <div class="as-perk-icon">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
      </div>
      <div class="as-perk-text">
        <strong>Travel + food allowance</strong>
      </div>
    </div>
    <div class="as-perk-item">
      <div class="as-perk-icon">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      </div>
      <div class="as-perk-text">
        <strong>Transport at night for women</strong>
      </div>
    </div>
  </div>
</div>'''


def ijp_card():
    return '''<div class="as-ijp-container reveal">
  <div class="as-ijp-grid">
    <div class="as-ijp-box">
      <div class="as-ijp-title">
        <span class="as-ijp-step">1</span>
        <h4>How to make an IJP</h4>
      </div>
      <ul class="list-clean">
        <li>The HR Manager should use <em>3B. Internal Job Posting (IJP) Template</em> to notify the position internally</li>
        <li>The HR Manager should display the IJP on notice boards across organisation and share over electronic platforms</li>
        <li>The HR Manager should reach out to the reporting manager for any recommendation for promotion</li>
      </ul>
    </div>
    <div class="as-ijp-box">
      <div class="as-ijp-title">
        <span class="as-ijp-step">2</span>
        <h4>Who can apply for an IJP</h4>
      </div>
      <ul class="list-clean">
        <li>Completed at least 12 months in the current role</li>
        <li>Not under a performance improvement plan</li>
        <li>No live disciplinary case</li>
      </ul>
      <p class="as-ijp-note">*Note that every internal candidate will also have to go through the same interview process as listed in the flowchart above.</p>
    </div>
    <div class="as-ijp-box">
      <div class="as-ijp-title">
        <span class="as-ijp-step">3</span>
        <h4>How to apply for an IJP</h4>
      </div>
      <ul class="list-clean">
        <li>Check the Internal Job postings notice board and electronic platforms</li>
        <li>Apply for the position by filling up 3C. Internal Job Posting Application Form</li>
        <li>Email the form to the HR Manager</li>
      </ul>
    </div>
    <div class="as-ijp-box">
      <div class="as-ijp-title">
        <span class="as-ijp-step">4</span>
        <h4>Points to note</h4>
      </div>
      <ul class="list-clean">
        <li>The releasing manager should not intentionally hold/block an internal movement</li>
        <li>A notice period of up to 30 days is suggested for effective handover of responsibilities</li>
      </ul>
    </div>
  </div>
</div>'''


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
            if cid == 'ch7' and first == 'Dealership Goal':
                return smart_kpi_card(), 1
            if cid == 'ch7' and first == 'Sample email':
                return sample_email_card(), 1
            if cid == 'ch4' and first == 'Perks':
                return perks_card(), 1
            if cid == 'ch3' and first.startswith('How to make an IJP'):
                return ijp_card(), 1
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
            if cid == 'ch13' and first.startswith('Potential'):
                return talent_grid(b['t']), 1
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
        if cid == 'ch11' and t.startswith('Manpower Attrition ='):
            return attrition_card(bl, i)
        if cid == 'ch6' and t.startswith('Learning design should be scientifically driven'):
            n = 0
            while bl[i + 1 + n]['num']: n += 1
            assert n == 5, n
            import v9extras as X9
            return f'<p>{b["html"]}</p>' + X9.learning_design(texts_after(bl, i, 5)), 1 + n
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
            return f'<p>{b["html"]}</p>' + fc.spot(texts_after(bl, i, 3), 'Spot Recognition'), 4
        return None
    return hook
