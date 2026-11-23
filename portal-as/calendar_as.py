"""9.1.2 annual calendar for the Service manual: every dated item comes from the docx's own tables / shapes."""
import re
import asdoc  # noqa
import build as B
import infographics as G


def rows_of(t):
    return [[c.text.strip() for c in B.cells_of(r)] for r in t.rows]


def tables(chunks, title):
    return [rows_of(b['t']) for b in chunks[title]['blocks'] if b['k'] == 'tbl']


def events(ctx):
    ch = ctx['chunks']
    E = []
    ee = 'Employee Engagement, Rewards and Recognition'
    eng = next(r for r in tables(ch, ee) if r[0][0] == 'Activity')
    for act, guide, purpose, by, att in [r[:5] for r in eng[1:]]:
        when = guide.split('When – ')[-1].strip()
        rule = None
        if '1st week of the next month' in when: rule = {'m': 'all', 'day': None}
        elif '7th April' in when: rule = {'m': 3, 'day': 7}
        elif '2nd October' in when: rule = {'m': 9, 'day': 2}
        if rule:
            E.append({**rule, 'title': act.replace('\n', ' '), 'category': 'engagement', 'freq': guide.replace('\n', ' · ').strip(' ·'),
                      'audience': att, 'chapter': 'ch9-1', 'chapterLabel': 'Ch.9 · 9.1 Employee Engagement Activities',
                      'desc': f'Purpose: {purpose} · Arranged by: {by}'})
    E.append({'m': 11, 'day': None, 'title': 'Employee Engagement Calendar is published in December month of the previous year', 'category': 'engagement',
              'freq': 'December month of the previous year', 'audience': 'All', 'chapter': 'ch9-1',
              'chapterLabel': 'Ch.9 · 9.1 Employee Engagement Activities',
              'desc': 'Employee Engagement Calendar is published in December month of the previous year on digital platforms and also placed on the notice board'})
    for tb in [r for r in tables(ch, ee) if r[0][0] == 'Award']:
        hdr = tb[0]
        wi = next(i for i, h in enumerate(hdr) if h.startswith('When to give award'))
        ri = next(i for i, h in enumerate(hdr) if re.match(r'Applicable|Role ?holders', h))
        for r in tb[1:]:
            when = r[wi].replace('\n', ' ')
            m = re.match(r'(1st|3rd) Friday of the (N\+1 month|1st month of the N\+1 QTR)', when)
            if not m:
                continue
            n = 1 if m.group(1) == '1st' else 3
            months = 'all' if 'N+1 month' in when else [0, 3, 6, 9]
            E.append({'m': months, 'nth': [n, 5], 'day': None, 'title': r[0].replace('\n', ' '), 'category': 'recognition',
                      'freq': when, 'audience': r[ri].replace('\n', ' '), 'chapter': 'ch9-2',
                      'chapterLabel': 'Ch.9 · 9.2 Rewards and Recognition', 'desc': r[1].replace('\n', ' ')})
    inc = next(r for r in tables(ch, 'Compensation, Benefits and Incentive Policy') if r[0][0] == 'Date')
    for date, act, who in inc[1:]:
        day = int(re.search(r'\d+', date).group(0))
        E.append({'m': 'all', 'day': day, 'title': act, 'category': 'incentive', 'freq': f'{date} of every month',
                  'audience': who, 'chapter': 'ch4-4', 'chapterLabel': 'Ch.4 · 4.4 Incentive Scheme',
                  'desc': 'It is a monthly performance reward program for achieving business targets.'})
    # performance reviews: the cycle shape (who / when) and the 7.1 table (what happens) in chapter 7
    pm = ch['Performance Management']['blocks']
    cyc = next(g for b in pm if b['k'] == 'shape' for g in b['groups'] if 'STEP 1' in ' '.join(' '.join(s['paras']) for s in g))
    stages = {int(s['paras'][0].split()[1]): s['paras'] for s in cyc if s['prst'] == 'ellipse' and s['paras'] and s['paras'][0].startswith('STEP')}
    what = {r[1]: r[2] for r in next(t for t in tables(ch, 'Performance Management') if t[0][0] == 'Step')[1:]}
    MON = {'April': 3, 'June': 5, 'December': 11, 'September': 8, 'March': 2}
    for n, p in stages.items():
        title, who, when = p[1], p[2], p[3]
        months = [MON[m] for m in re.findall(r'April|June|December|September|March', when)]
        if n == 5:
            continue
        for m in months:
            E.append({'m': m, 'day': None, 'title': title, 'category': 'reviews', 'freq': when, 'audience': who,
                      'chapter': 'ch7-1', 'chapterLabel': 'Ch.7 · 7.1 Career Driven Performance Management', 'desc': what.get(title, '')})
    # training calendar finalisation: the cards that state a timeline
    import hooks
    blocks = [b for b in ch['Learning and Development']['blocks'] if b['k'] == 'shape']
    for b in blocks:
        for grp in b['groups']:
            if 'Training Calendar Finalisation Process' in ' '.join(' '.join(s['paras']) for s in grp):
                title, cards = hooks.calendar_cards(grp)
                for head, bullets in cards:
                    tl = next((x for x in bullets if x.startswith('Timelines')), None)
                    if not tl:
                        continue
                    dm = re.search(r'(\d+)(?:st|nd|rd|th)', tl)
                    day = int(dm.group(1)) if dm and 'of every month' in tl and 'Within' not in tl and 'to' not in tl else None
                    E.append({'m': 'all', 'day': day, 'title': head, 'category': 'training', 'freq': tl, 'audience': 'IDT',
                              'chapter': 'ch6-3', 'chapterLabel': 'Ch.6 · 6.3 Monthly In-house Training Calendar Planning Process',
                              'desc': ' · '.join(x for x in bullets if x != tl)})
    return E


def build(T, ctx, tbl_block):
    rows = rows_of(tbl_block['t'])[1:]
    assert len(rows) == 12
    themes = [(t, p, a) for _, t, p, a in rows]
    return G.calendar(T, themes, events(ctx))
