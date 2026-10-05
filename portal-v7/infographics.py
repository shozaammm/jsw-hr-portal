"""Portal infographics refilled with V7 text.

Each builder loads the ORIGINAL component markup from the pre-V7 portal
(v2.html @ BASE_COMMIT) and swaps in V7 wording, so the design is the
portal's own. No wording here is invented: every string is passed in by
build.py from the V7 docx (text paragraphs, tables, or the text printed
inside V7's own images).
"""
import copy, html, json, re
from bs4 import BeautifulSoup

esc = lambda s: html.escape(s, quote=False)

W = ['zigzag', 'lj-card', 'calendar-hub', 'jsw-interactive-card', 'enquiry-flow', 'career-routes-matrix',
     'img-card', 'rf-flow', 'pipe-chips', 'row-2col']


class Templates:
    """Infographics of the pre-V7 portal, in document order (1-based, as catalogued)."""
    def __init__(self, base_html):
        self.base = base_html
        s = BeautifulSoup(base_html, 'html.parser')
        self.items = []
        for sid in ['ch3', 'ch4', 'ch5', 'ch6', 'ch7', 'ch8', 'ch9', 'ch10', 'ch11']:
            for el in s.find(id=sid).find_all(class_=W):
                if el.find_parent(class_=W) or el.find_parent(style=re.compile(r'display:\s*none')):
                    continue
                self.items.append(el)

    def get(self, n):
        return copy.copy(BeautifulSoup(str(self.items[n - 1]), 'html.parser'))

    def calendar_assets(self):
        i = self.base.find("var MONTH_NAMES=['January'")
        s = self.base.rfind('<script', 0, i)
        e = self.base.find('</script>', i) + len('</script>')
        m = self.base.find('id="calEventModal"')
        ms = self.base.rfind('<div', 0, m)
        depth, me = 0, ms
        for t in re.finditer(r'<(/?)div\b', self.base[ms:]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                me = self.base.find('>', ms + t.end()) + 1
                break
        return self.base[s:e], self.base[ms:me]


def _set(tag, text):
    tag.clear()
    tag.append(text)


# ── 3.1 recruitment: rf-flow phases (A–L, four per row as in V7's table) ──
def rf_flow(T, steps):
    """steps: [(letter, text, roles[list], rms[bool])]"""
    s = T.get(1)
    flow = s.find(class_='rf-flow')
    phase_tpl = copy.copy(flow.find(class_='rf-phase'))
    card_tpl = copy.copy(phase_tpl.find(class_='rf-step-card'))
    flow.clear()
    for k in range(0, len(steps), 4):
        chunk = steps[k:k + 4]
        ph = copy.copy(phase_tpl)
        ph.find(class_='rf-phase-header').decompose()   # V7 has no group label for these rows
        grid = ph.find(class_='rf-steps-grid')
        grid.clear()
        for letter, text, roles, rms in chunk:
            c = copy.copy(card_tpl)
            if rms:
                c['class'] = c['class'] + ['zz-rms']
            _set(c.find(class_='rf-step-num'), letter)
            role = c.find(class_='rf-step-role')
            role.clear()
            for j, r in enumerate(roles):
                if j:
                    role.append(s.new_tag('br'))
                role.append(r)
            _set(c.find(class_='rf-step-text'), text)
            grid.append(c)
        flow.append(ph)
    return str(s)


# ── 4.2 salary advance: four-point cycle ──
def cycle4(T, items, centre):
    s = T.get(4)
    card = s.find(class_='jsw-interactive-card')
    card.find(class_='jsw-card-header').decompose()
    texts = [d for d in card.find_all('div') if d.get('style', '').startswith("font-family:'Manrope',sans-serif;font-weight:700;font-size:16px")]
    assert len(texts) == 4
    for d, t in zip(texts, items):
        _set(d, t)
    c = card.find(string=re.compile('4-Step')).parent
    c.clear()
    for j, w in enumerate(centre):
        if j:
            c.append(s.new_tag('br'))
        c.append(w)
    return str(s)


# ── 6.1 learner's journey (V7 image rId21) ──
def learner_journey(T, cards, caption=None):
    """cards: [{title, subtitle, steps:[(badge, body)], chips:[chip-after-step-i or None], end_chip}]"""
    s = T.get(10)
    fig = s.find('figure')
    track = fig.find(class_='lj-track-container')
    card_tpl = copy.copy(track.find(class_='lj-card'))
    step_tpl = copy.copy(card_tpl.find(class_='lj-step'))
    conn_tpl = copy.copy(card_tpl.find(class_='lj-connector'))
    track.clear()
    for cd in cards:
        c = copy.copy(card_tpl)
        _set(c.find(class_='lj-title'), cd['title'])
        _set(c.find(class_='lj-subtitle'), cd['subtitle'])
        foot = c.find(class_='lj-footer-note')
        if foot:
            foot.decompose()
        wrap = c.find(class_='lj-steps-wrap')
        wrap.clear()
        n = len(cd['steps'])
        for i, (badge, body) in enumerate(cd['steps']):
            st = copy.copy(step_tpl)
            _set(st.find(class_='lj-step-badge'), badge)
            _set(st.find(class_='lj-step-body'), body)
            wrap.append(st)
            chip = cd['chips'][i] if i < len(cd['chips']) else None
            if i < n - 1 or chip:
                cn = copy.copy(conn_tpl)
                ch = cn.find(class_='lj-assessment-chip')
                if chip:
                    _set(ch, chip)
                elif ch:
                    ch.decompose()
                wrap.append(cn)
        track.append(c)
    cap = fig.find('figcaption')
    if caption:
        _set(cap, caption)
    else:
        cap.decompose()
    return str(s)


# ── 6.2 TMS steps (V7 image rId22) → numbered vertical flow ──
def step_flow(T, steps, caption=None):
    s = T.get(33)
    fig = s.find('figure')
    flow = fig.find(class_='enquiry-flow')
    cards = flow.find_all(class_='enquiry-card')
    tpl_a, tpl_b = copy.copy(cards[0]), copy.copy(cards[1])
    arrow = copy.copy(cards[0].find_next_sibling('div'))
    flow.clear()
    for i, (head, body) in enumerate(steps):
        c = copy.copy(tpl_a if i % 2 == 0 else tpl_b)
        divs = c.find_all('div', recursive=False)
        _set(divs[0], head)
        _set(divs[1], body)
        flow.append(c)
        if i < len(steps) - 1:
            flow.append(copy.copy(arrow))
    cap = fig.find('figcaption')
    if caption:
        _set(cap, caption)
    elif cap:
        cap.decompose()
    return str(s)


# ── 6.3 calendar finalisation (V7 image rId24) → module cards ──
def module_cards(T, title, cards):
    """cards: [(head, [bullets])] in V7 order."""
    s = T.get(11)
    fig = s.find('figure')
    dash = fig.find(class_='tna-dashboard')
    sec_tpl = copy.copy(dash.find(class_='tna-phase-section'))
    card_tpl = copy.copy(sec_tpl.find(class_='tna-mod-card'))
    dash.clear()
    sec = copy.copy(sec_tpl)
    pt = sec.find(class_='tna-phase-title')
    pt.clear()
    sp = s.new_tag('span'); sp.string = title
    pt.append(sp)
    grid = sec.find(class_='tna-modules-grid')
    grid.clear()
    if len(cards) == 8:     # V7's picture runs as a snake: 1→2→3 ↓ 4←5←6 ↓ 7→8
        grid['class'] = grid['class'] + ['v7-snake']
    for i, (head, bullets) in enumerate(cards):
        c = copy.copy(card_tpl)
        h = c.find(class_='tna-mod-head')
        h.clear()
        a = s.new_tag('span'); a.string = head
        h.append(a)
        b = s.new_tag('span', attrs={'style': 'font-size:10px;opacity:0.8;font-weight:400'})
        b.string = f'{i + 1:02d}'
        h.append(b)
        h['class'] = ['tna-mod-head'] + (['accent'] if i == 0 else [])
        ul = c.find('ul')
        ul.clear()
        for t in bullets:
            li = s.new_tag('li'); li.string = t
            ul.append(li)
        grid.append(c)
    dash.append(sec)
    for cap in fig.find_all('figcaption'):
        cap.decompose()
    return str(s)


# ── 6.7 what IDT reports: ring with one segment per category ──
def ring(T, centre, cats):
    """cats: [(heading, [bullets])]"""
    s = T.get(14)
    card = s.find(class_='jsw-interactive-card')
    card.find(class_='jsw-card-header').decompose()
    shades = ['#0A0A0A', '#6E6E6E', '#D0D0D0']
    n = len(cats)
    stops = ','.join(f'{shades[i]} {360 * i / n:.0f}deg {360 * (i + 1) / n:.0f}deg' for i in range(n))
    donut = card.find('div', style=re.compile('conic-gradient'))
    donut['style'] = re.sub(r'conic-gradient\([^;]*\);', f'conic-gradient(from -90deg,{stops});', donut['style'])
    c = card.find(string=re.compile('Report')).parent
    c.clear()
    for j, w in enumerate(centre):
        if j:
            c.append(s.new_tag('br'))
        c.append(w)
    rows = donut.find_next_sibling('div').find_all('div', recursive=False)
    for row in rows[n:]:
        row.decompose()
    for row, (head, bullets) in zip(rows, cats):
        t = row.find('div', style=re.compile('text-transform:uppercase'))
        _set(t, head)
        _set(t.find_next_sibling('div'), ' · '.join(bullets))
    return str(s)


# ── 6.6 LMS: chevron strip (V7 image rId27) ──
def chevrons(T, items):
    """items: [(label, text)]"""
    s = T.get(24)
    card = s.find(class_='jsw-interactive-card')
    card.find(class_='jsw-card-header').decompose()
    strip = card.find('div', style=re.compile('drop-shadow'))
    chev = strip.find_all('div', recursive=False)
    labels = strip.find_next_sibling('div')
    lab = labels.find_all('div', recursive=False)
    n = len(items)
    grads = ['linear-gradient(120deg,#454545 0%,#0a0a0a 45%,#000000 100%)',
             'linear-gradient(120deg,#5c5c5c 0%,#2e2e2e 45%,#141414 100%)',
             'linear-gradient(120deg,#7a7a7a 0%,#505050 45%,#2c2c2c 100%)',
             'linear-gradient(120deg,#9a9a9a 0%,#747474 45%,#4a4a4a 100%)',
             'linear-gradient(120deg,#c3c3c3 0%,#a3a3a3 45%,#787878 100%)']
    while len(chev) < n:
        chev.append(copy.copy(chev[-1])); strip.append(chev[-1])
        lab.append(copy.copy(lab[-1])); labels.append(lab[-1])
    w = 1280
    cw = round((w + 35 * (n - 1)) / n)
    for i, (c, l, (label, text)) in enumerate(zip(chev, lab, items)):
        c['style'] = re.sub(r'width:\d+px', f'width:{cw}px', c['style'])
        c['style'] = re.sub(r'background:linear-gradient\([^;]*\);', f'background:{grads[i]};', c['style'])
        num = c.find('div', style=re.compile('font-size:32px'))
        _set(num, label)
        num['style'] = num['style'].replace('font-size:32px', 'font-size:28px')
        _set(l, text)
    labels['style'] = re.sub(r'repeat\(\d+,1fr\)', f'repeat({n},1fr)', labels['style'])
    return str(s)


# ── 7.1 SMART ──
def smart(T, rows):
    """rows: [(letter, word, text)]"""
    s = T.get(18)
    card = s.find(class_='jsw-interactive-card')
    card.find(class_='jsw-card-header').decompose()
    tiles = card.find(class_='jsw-card-body').find('div').find_all('div', recursive=False)
    for tile, (letter, word, text) in zip(tiles, rows):
        d = tile.find_all('div', recursive=False)
        _set(d[0], letter); _set(d[1], word); _set(d[2], text)
    return str(s)


# ── 7.1 review points: numbered cards ──
def review_cards(T, items):
    s = T.get(19)
    card = s.find(class_='jsw-interactive-card')
    card.find(class_='jsw-card-header').decompose()
    grid = card.find(class_='jsw-myr-grid')
    tpls = grid.find_all(class_='jsw-myr-item')
    icons2 = BeautifulSoup(str(T.get(20)), 'html.parser').find_all(class_='jsw-myr-item')
    pool = tpls + icons2
    for c in grid.find_all(string=lambda t: isinstance(t, type(t)) and t.__class__.__name__ == 'Comment'):
        c.extract()
    grid.clear()
    for i, text in enumerate(items):
        it = copy.copy(pool[i % len(pool)])
        _set(it.find(class_='jsw-myr-badge'), f'{i + 1:02d}')
        it.find(class_='jsw-myr-title').decompose()
        _set(it.find(class_='jsw-myr-desc'), text)
        grid.append(it)
    return str(s)


# ── 8.1 career routes matrix ──
def career_matrix(T, rows, caption):
    s = T.get(21)
    fig = s.find('figure')
    table = fig.find('table')
    th_tpl = copy.copy(table.find('th'))
    tr = table.find('tbody').find('tr')
    td_role = copy.copy(tr.find_all('td')[0])
    td_cells = [copy.copy(td) for td in tr.find_all('td')[1:]]
    head, body = rows[0], rows[1:]
    thr = table.find('thead').find('tr'); thr.clear()
    for h in head:
        th = copy.copy(th_tpl)
        th.clear()
        for j, part in enumerate(h.split('\n')):
            if j:
                th.append(s.new_tag('br'))
            th.append(part)
        thr.append(th)
    tb = table.find('tbody'); tb.clear()
    for r in body:
        row = s.new_tag('tr')
        a = copy.copy(td_role); _set(a, r[0]); row.append(a)
        for k, v in enumerate(r[1:]):
            c = copy.copy(td_cells[min(k, len(td_cells) - 1)])
            _set(c, v if v.strip() else '—')
            row.append(c)
        tb.append(row)
    for el in fig.find_all(['p', 'figcaption']):
        el.decompose()
    for el in fig.find_all('div', class_=lambda c: not c or 'career-routes-matrix' not in c):
        if el.parent is fig:
            el.decompose()
    cap = s.new_tag('figcaption', attrs={'class': 'img-caption'})
    cap.string = caption
    fig.append(cap)
    return str(s)


# ── 9.2 spot recognition: star with V7's examples ──
def spot(T, items, centre):
    s = T.get(26)
    card = s.find(class_='jsw-interactive-card')
    card.find(class_='jsw-card-header').decompose()
    root = card.find('div', style=re.compile('position:relative'))
    boxes = [d for d in root.find_all('div', recursive=False) if 'width:280px' in d.get('style', '')]
    svg = root.find('svg')
    lines, dots = svg.find_all('line'), svg.find_all('circle')
    keep = {3: [0, 2, 3], 4: [0, 1, 2, 3], 5: [0, 1, 2, 3, 4]}[len(items)]
    for i in range(len(boxes)):
        if i not in keep:
            boxes[i].decompose(); lines[i].decompose(); dots[i].decompose()
    for k, (i, text) in enumerate(zip(keep, items)):
        num = boxes[i].find('div', style=re.compile('font-size:16px;color:#0A0A0A'))
        _set(num, f'{k + 1:02d}')
        _set(boxes[i].find_all('div', recursive=False)[-1], text)
    _set(card.find(string='SPOT').parent, centre)
    return str(s)


# ── 9.1 engagement calendar ──
CAL_CATS = {
    'engagement':  {'label': 'Employee Engagement', 'cls': 'townhall'},
    'recognition': {'label': 'Rewards and Recognition', 'cls': 'recruitment'},
    'incentive':   {'label': 'Incentive Scheme', 'cls': 'incentive'},
    'reviews':     {'label': 'Performance Reviews', 'cls': 'appraisal'},
    'training':    {'label': 'Training Calendar', 'cls': 'training'},
}


def calendar(T, themes, events):
    """themes: 12 × (theme, pillar, activity) from V7 9.1.2.
    events: dicts {m: month idx | 'all' | [idx…], day: int | None, nth: [n, weekday] | None,
                   title, category, freq, audience, chapter, chapterLabel, desc} — all text from V7."""
    js, modal = T.calendar_assets()
    hub = str(T.get(25))
    month_themes = json.dumps([{'theme': f'{t} · {p}', 'desc': f'Sample Activity: {a}'} for t, p, a in themes], ensure_ascii=False)
    cats = json.dumps({k: {'label': v['label'], 'dot': {'townhall': 'var(--grey-300)', 'recruitment': 'var(--ink)',
                                                        'incentive': 'var(--gold)', 'appraisal': 'var(--ink)',
                                                        'training': 'var(--gold-lite)'}[v['cls']], 'cls': v['cls']}
                       for k, v in CAL_CATS.items()}, ensure_ascii=False)
    rules = json.dumps(events, ensure_ascii=False)
    a = js.find('  var MONTH_THEMES=[')
    b = js.find('  var QUARTER_LOAD=')
    b = js.find('\n', b) + 1
    js = js[:a] + f'''  var MONTH_THEMES={month_themes};
  var CATS={cats};
  // V7 rules → per-year events. day: fixed date; nth: [n, weekday] (e.g. 3rd Friday); neither: month-level item
  var RULES={rules};
  function nthWeekday(y,m,n,wd){{var d=new Date(y,m,1);var off=(wd-d.getDay()+7)%7;return 1+off+(n-1)*7;}}
  function eventsFor(y,m){{
    return RULES.filter(function(r){{return r.m==='all'||r.m===m||(Array.isArray(r.m)&&r.m.indexOf(m)>-1);}})
      .map(function(r){{var e={{}};for(var k in r)e[k]=r[k];e.day=r.nth?nthWeekday(y,m,r.nth[0],r.nth[1]):(r.day||null);return e;}});
  }}
''' + js[b:]
    js = js.replace("function catClass(c){return 'ch-pill cat-'+c;}", "function catClass(c){return 'ch-pill cat-'+CATS[c].cls;}")
    js = js.replace("var max=Math.max.apply(null,QUARTER_LOAD);",
                    "var LOAD=MONTH_NAMES.map(function(_,i){return eventsFor(state.year,i).length;});var max=Math.max.apply(null,LOAD)||1;")
    js = js.replace("var h=Math.round(QUARTER_LOAD[i]/max*30)+4;", "var h=Math.round(LOAD[i]/max*30)+4;")
    js = js.replace("var events=(EVENTS[i]||[]).filter(function(e){return state.filter==='all'||e.category===state.filter;});",
                    "var events=eventsFor(state.year,i).filter(function(e){return state.filter==='all'||e.category===state.filter;});")
    js = js.replace("var dots=(EVENTS[i]||[]).map(function(e){return '<span class=\"ch-dot\" style=\"background:'+CATS[e.category].dot+'\"></span>';}).join('');",
                    "var seen={};var dots=eventsFor(state.year,i).filter(function(e){if(seen[e.category])return false;seen[e.category]=1;return true;}).map(function(e){return '<span class=\"ch-dot\" title=\"'+CATS[e.category].label+'\" style=\"background:'+CATS[e.category].dot+'\"></span>';}).join('');")
    js = js.replace("var evs=(!c.outside?(EVENTS[state.month]||[]).filter(function(e){return e.day===c.day;}):[]);",
                    "var evs=(!c.outside?eventsFor(state.year,state.month).filter(function(e){return e.day===c.day;}):[]);")
    js = js.replace("document.getElementById('chMonthGrid').innerHTML=html;",
                    "document.getElementById('chMonthGrid').innerHTML=html;\n    renderMonthNotes();")
    js = js.replace("var items=(EVENTS[i]||[]).map(function(e){return '<div>'+e.day+' — '+esc(e.title)+'</div>';}).join('');",
                    "var items=eventsFor(state.year,i).map(function(e){return '<div>'+(e.day?e.day+' — ':'')+esc(e.title)+'</div>';}).join('');")
    js = js.replace("var ev=(EVENTS[monthIdx]||[]).find(function(e){return e.day===day&&e.title===title;});",
                    "var ev=eventsFor(state.year,monthIdx).find(function(e){return (e.day||0)===day&&e.title===title;});")
    js = js.replace("'+MONTH_NAMES[monthIdx]+' '+ev.day+', '+state.year+'", "'+MONTH_NAMES[monthIdx]+(ev.day?' '+ev.day:'')+', '+state.year+'")
    js = js.replace("""      '<div class="ce-row"><span class="ce-label">Resources</span><a class="ce-link" href="#" onclick="return false">Download checklist / guideline</a><br>'+
      '<a class="ce-link" href="#'+ev.chapter+'" onclick="chCloseEventModal()">'+esc(ev.chapterLabel)+' →</a></div>';""",
                    """      '<div class="ce-row"><span class="ce-label">Chapter</span><a class="ce-link" href="#'+ev.chapter+'" onclick="chCloseEventModal()">'+esc(ev.chapterLabel)+' →</a></div>';""")
    js = js.replace("  window.chSetView=function(v){", """  function renderMonthNotes(){
    var el=document.getElementById('chMonthNotes'); if(!el) return;
    var evs=eventsFor(state.year,state.month).filter(function(e){return !e.day;});
    el.innerHTML=evs.length?'<span class="ch-notes-label">This month</span>'+evs.map(function(e){
      var dim=(state.filter!=='all'&&state.filter!==e.category)?' dim':'';
      return '<div class="'+catClass(e.category)+dim+'" onclick="chOpenEvent('+state.month+',0,\\''+e.title.replace(/'/g,"\\\\'")+'\\')">'+esc(e.title)+'</div>';
    }).join(''):'';
  }
  window.chSetView=function(v){""")
    for bad in ('EVENTS[', 'QUARTER_LOAD'):
        assert bad not in js.replace('var RULES', ''), bad
    hub = hub.replace('<div class="ch-weekday-row">', '<div class="ch-month-notes" id="chMonthNotes"></div>\n<div class="ch-weekday-row">')
    assert 'chMonthNotes' in hub
    return hub + '\n' + modal + '\n' + js
