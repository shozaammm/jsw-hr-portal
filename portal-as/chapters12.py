"""Chapter 1 (organisation charts) and chapter 2 (job descriptions) for the Service manual."""
import base64, html, re
import asdoc  # noqa
import build as B
import jd as JD
import service_data as S

esc = lambda s: html.escape(s, quote=False)
escq = lambda s: html.escape(s, quote=True)

JD_ANNEX = [('2A', 'Job Description Template'), ('2B', 'All Job Descriptions'), ('2C', 'Competencies')]
LBL = re.compile(r'^:?\s*(Objective|Purpose|Principles|Benefits?\s+(?:for|to)\s+(?:the\s+)?(?:Dealers?|Dealerships?|Customers?))\s*:?\s*$', re.I)


def opener(blocks):
    """Split a chapter opener into its labelled lists. Returns (pull, {label: [items]}, rest_blocks)."""
    pull, lab, out, order, i = None, None, {}, [], 0
    while i < len(blocks):
        b = blocks[i]
        if b['k'] != 'p' or b['lvl'] == 2:
            break
        t = b['text']
        if t.strip() == ':':
            i += 1; continue
        if b['style'] == 'Intense Quote' or (pull is None and t[:1] in '"“' and not b['num']):
            pull = t; i += 1; continue
        m = LBL.match(t)
        if m:
            key = m.group(1).lower()
            key = 'dealer' if re.search(r'dealer', key) else 'customer' if re.search(r'customer', key) else key
            lab = key; out.setdefault(key, []); order.append(key); i += 1; continue
        if lab is None:
            break
        if lab != 'principles' and not b['num']:
            break
        out[lab].append(b)
        i += 1
    return pull, out, order, blocks[i:]


def meta_html(label, items, solo=False):
    lis = ''.join(f'<li>{x}</li>' for x in items)
    return (f'<div class="meta-item"><span class="eyebrow">{esc(label)}</span>'
            f'<ul class="list-clean" style="margin-top:4px;">{lis}</ul></div>')


ICONS = {
    'Role Clarity': '<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 11l2 2 4-4"/>',
    'Efficient Decision Making': '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="12" r="2"/><path d="M6 7v10"/><path d="M6 12h10"/>',
    'Enhanced Collaboration': '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.4"/><path d="M16.5 14.2A5 5 0 0 1 21 19"/>',
    'Resource Optimization': '<path d="M4 15a8 8 0 0 1 16 0"/><path d="M12 15l4-5"/><circle cx="12" cy="15" r="1.2"/>',
}


def org_principles(blocks):
    """'A robust organizational structure …:' then four 'Heading:' + two bullets each -> the portal's ig-pr cards."""
    intro, cards, cur = [], [], None
    for b in blocks:
        t = b['text']
        if b['num']:
            cur[1].append(b['html'])
        elif t.endswith(':') and len(t) < 40:
            cur = [t, []]; cards.append(cur)
        else:
            intro.append(b)
    out = ''.join(
        '<div class="ig-pr-card" role="listitem"><div class="ig-pr-head"><span class="ig-ico" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS[h.rstrip(":")]}</svg></span><h4 class="ig-pr-title">{esc(h)}</h4></div>'
        '<ul class="list-clean">' + ''.join(f'<li>{x}</li>' for x in items) + '</ul></div>' for h, items in cards)
    return intro, f'<div class="ig-pr" role="list">{out}</div>'


def opener_html(pull, out, order, bl, principle_html=None):
    parts = []
    if pull:
        parts.append(f'<div class="pull">{esc(pull)}</div>')
    first = out.get('objective') or out.get('purpose')
    flabel = 'Objective:' if out.get('objective') else 'Purpose:'
    parts.append('<div class="meta-row reveal" data-solo="1" style="margin-top:14px; padding-top:16px;">'
                 + meta_html(flabel, [b['html'] for b in first]) + '</div>')
    row = ''
    if out.get('dealer'):
        row += meta_html('Benefit to Dealer:', [b['html'] for b in out['dealer']])
    if out.get('customer'):
        row += meta_html('Benefit to Customer:', [b['html'] for b in out['customer']])
    parts.append(f'<div class="meta-row reveal" style="margin-top:14px; padding-top:16px;">{row}</div>')
    if principle_html:
        parts.append(principle_html)
    return '\n'.join(parts)


# ───────────────────────── chapter 1: organisation ─────────────────────────
def build_org(D, chunks, head):
    bl = chunks['Dealership Organisation Structure']['blocks']
    pull, out, order, rest = opener(bl)
    # Principles block = principles sentence + 4 headed lists
    pr_intro, pr_cards = org_principles(out['principles'])
    pr = '<h3 class="sub-title subhead">Principles</h3>\n' + ''.join(f'<p>{b["html"]}</p>' for b in pr_intro) + '\n' + pr_cards
    body = opener_html(pull, out, order, rest, pr)
    h2 = rest[0]; assert h2['lvl'] == 2
    note = rest[1]['html']
    a = head.find('<div class="orgchart-stage"', head.find('id="chap-ch2"'))
    e = head.find('<div class="tree-store"', a)
    stage = head[a:e]
    body += (f'\n<h3 class="sub-title subhead" id="ch2-1">1.1 {esc(h2["text"])}</h3>\n<p><em>{note}</em></p>\n\n'
             + stage + S.tree_stores() + '\n<div style="display:none"></div>')
    subs = [('ch2-1', '1.1 ' + h2['text'])]
    return B.article('ch2', 'CHAPTER 1', 'Dealership Organisation Structure', body), subs


# ───────────────────────── chapter 2: job descriptions ─────────────────────────
ACR = {'EDP', 'CRM', 'CRE', 'PDI', 'SA', 'AXS', 'DE', 'P&D'}


def display(title):
    if not title.isupper():
        return title
    def w(tok):
        if tok.strip('()') in ACR:
            return tok
        return '/'.join('-'.join(p.capitalize() for p in q.split('-')) for q in tok.split('/')) if tok != '&' else tok
    return ' '.join(w(t) for t in title.split(' '))


def initials(name):
    toks = [t for t in re.split(r'[\s/&\-]+', re.sub(r'\(.*?\)', '', name)) if t and t.lower() not in ('of', 'and')]
    return (toks[0][0] + (toks[1][0] if len(toks) > 1 else '')).upper() if toks else '?'


def avatar(name):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" fill="#d9d9dd"/>'
           f'<text x="40" y="49" font-family="Helvetica,Arial,sans-serif" font-size="28" font-weight="700" text-anchor="middle" fill="#3b3b40">{esc(initials(name))}</text></svg>')
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()


def jd_detail(role):
    name = display(role['title'])
    meta = ''.join(f'<div class="rd-meta-item"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k, v in role['meta'])
    out = [f'<div class="rd-detail-header"><img class="rd-avatar-lg" src="{avatar(name)}" alt=""><div><h3 class="rd-detail-title">{esc(name)}</h3></div></div>',
           f'<div class="rd-meta-row">{meta}</div>']
    ul = lambda xs: '<ul class="list-clean">' + ''.join(f'<li>{esc(x)}</li>' for x in xs) + '</ul>'
    chips = lambda xs: '<div class="chip-row">' + ''.join(f'<span class="chip">{esc(x)}</span>' for x in xs) + '</div>'
    for s in role['sections']:
        out.append(f'<h4 class="rd-sub">{esc(s["name"])}</h4>')
        nm = s['name']
        if nm == 'Position Overview':
            out.append(''.join(f'<p class="rd-overview">{esc(x)}</p>' for x in s['items']))
        elif re.search(r'Education|Experience|Competencies', nm):
            out.append(chips(s['items']))
        elif 'Key Responsibilities' in nm:
            if s['items']:
                out.append(ul(s['items']))
            for g in s['groups']:
                out.append(f'<div class="rd-resp-head">{esc(g["name"])}</div>' + (ul(g['items']) if g['items'] else ''))
        else:   # KPIs
            if s['items']:
                out.append(f'<div class="rd-kpi-group">{ul(s["items"])}</div>')
            for g in s['groups']:
                out.append(f'<div class="rd-kpi-group"><div class="rd-kpi-title">{esc(g["name"])}</div>{ul(g["items"])}</div>')
    return ''.join(out)


def build_jd(D, chunks, docs):
    roles, notes = JD.parse(docs[0])
    # Paint Technician: its "Education" heading sits inside Position Overview (source formatting) -> its own section
    for r in roles:
        secs = []
        for s in r['sections']:
            if s['name'] == 'Position Overview' and any(g['name'] == 'Education' for g in s['groups']):
                g = next(g for g in s['groups'] if g['name'] == 'Education')
                s['groups'].remove(g)
                secs.append(s); secs.append({'name': 'Education', 'items': g['items'], 'groups': []})
                continue
            # a leftover reviewer note in the source (red, not role content)
            s['groups'] = [g for g in s['groups'] if not g['name'].startswith('BODYSHOP MANAGER TO BE ADDED')]
            secs.append(s)
        r['sections'] = secs
    bl = chunks['Job Descriptions']['blocks']
    pull, out, order, rest = opener(bl)
    pr = ''
    if out.get('principles'):
        items = [b['html'] for b in out['principles']]
        pr = ('<h3 class="sub-title subhead">Principles</h3>\n<ol class="pr-grid pr-n%d">' % len(items)
              + ''.join(f'<li class="pr-card"><span class="pr-num">{i:02d}</span><p>{x}</p></li>' for i, x in enumerate(items, 1)) + '</ol>')
    body = opener_html(pull, out, order, rest, pr)
    intro = next(b for b in rest if b['k'] == 'p' and b['text'].startswith('This chapter covers'))
    body += f'\n<p style="margin-top:14px;">{intro["html"]}</p>\n'
    store = '<div id="rdStore" style="display:none">\n' + ''.join(
        f'  <div id="rd-role-{i}">{jd_detail(r)}</div>\n' for i, r in enumerate(roles)) + '</div>\n'
    btns = ''.join(
        f'  <button class="rd-role-btn{" active" if i == 0 else ""}" data-role="{i}" onclick="rdSelect({i})" type="button">'
        f'<img alt="" class="rd-avatar-sm" loading="lazy" src="{avatar(display(r["title"]))}"><span class="rd-role-text">'
        f'<span class="rd-role-name">{esc(display(r["title"]))}</span><span class="rd-role-dept">{esc(dict(r["meta"]).get("Department", ""))}</span></span></button>\n'
        for i, r in enumerate(roles))
    body += store + ('<div class="role-directory reveal" id="ch1-roles">\n  <div class="rd-list" id="rdList">\n' + btns + '</div>\n'
                     '  <div class="rd-detail" id="rdDetail">' + jd_detail(roles[0]) + '</div>\n</div>\n')
    # annexure hint (non-interactive)
    body += ('<div class="chap-annexure-hint" id="ch1-annex" style="margin-top:32px"><h4 class="subhead" style="font-weight:700;margin-bottom:12px;">Annexure</h4>'
             '<div class="annex-file-list as-annex">' + ''.join(S.annex_item(c, t) for c, t in JD_ANNEX) + '</div></div>')
    return B.article('ch1', 'CHAPTER 2', 'Job Descriptions', body), roles, notes


def build(D, chunks, docs, head):
    ch2, subs2 = build_org(D, chunks, head)
    ch1, roles, notes = build_jd(D, chunks, docs)
    return ch2, ch1, {'ch2': subs2, 'ch1': []}
