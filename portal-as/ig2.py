"""More infographics for service.html.

Every word shown comes from the Service Word files: tables are re-laid as timelines, tiles, ladders and
cards from their own cells/headers; chapter openers get icons and numerals (no words added). A text check
asserts that no table gained a word it did not already have.
"""
import re
from bs4 import BeautifulSoup

CSS = '''<style id="as-ig2">
/* ── chapter numeral + section chips (Hyundai SOP chapter-opener idea) ── */
.jx-head-row{position:relative}
.as-ghost{position:absolute;right:4px;top:auto;bottom:-96px;font-size:clamp(80px,10vw,140px);font-weight:800;letter-spacing:-.05em;line-height:1;color:rgba(21,21,21,.07);pointer-events:none;user-select:none;font-variant-numeric:tabular-nums}
.as-secs{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 6px;padding:0}
.as-secs a{display:inline-flex;align-items:center;gap:10px;padding:9px 16px 9px 10px;border-radius:999px;background:#fff;border:1px solid rgba(0,0,0,.12);color:#151515;text-decoration:none;font-size:14.5px;font-weight:600;line-height:1.25;transition:transform .18s,box-shadow .18s,border-color .18s}
.as-secs a b{display:grid;place-items:center;min-width:34px;height:26px;padding:0 8px;border-radius:999px;background:#151515;color:#fff;font-size:12.5px;font-variant-numeric:tabular-nums}
.as-secs a:hover{transform:translateY(-1px);box-shadow:0 6px 16px rgba(0,0,0,.12);border-color:#151515}
/* ── objective / benefit cards ── */
#jxView .meta-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;border:0!important;padding:0!important;margin:20px 0!important}
#jxView .meta-row .meta-item{background:#fff;border:1px solid rgba(0,0,0,.1);border-radius:18px;padding:20px 22px;box-shadow:0 1px 0 rgba(0,0,0,.04)}
#jxView .meta-row[data-solo] .meta-item{background:#151515;color:#fff;border-color:#151515;grid-column:1/-1}
#jxView .meta-row[data-solo] .meta-item,#jxView .meta-row[data-solo] .meta-item li,#jxView .meta-row[data-solo] .meta-item .eyebrow span{color:#fff!important}
#jxView .meta-row .eyebrow{display:flex!important;align-items:center;gap:12px;margin:0 0 6px}
#jxView .meta-row .as-ico{flex:none;width:42px;height:42px;padding:9px;border-radius:12px;background:#151515;color:#fff;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
#jxView .meta-row[data-solo] svg.as-ico{background:#fff!important;color:#151515!important;stroke:#151515!important}
#jxView .meta-row .list-clean li{position:relative;padding-left:26px}
#jxView .meta-row .list-clean li::before{content:""!important;position:absolute!important;left:2px!important;top:.6em!important;width:11px!important;height:6px!important;border-left:2.5px solid #151515!important;border-bottom:2.5px solid #151515!important;transform:rotate(-45deg)!important;background:none!important;border-radius:0!important;opacity:1!important}
#jxView .meta-row[data-solo] .list-clean li::before{border-color:#fff!important}
/* ── fixes ── */
.jx-chapter .fx-chev-n{flex:0 0 26px!important;min-width:26px;aspect-ratio:1/1}
/* IJP: 4th card spans the row instead of sitting alone */
.as-ijp-grid .as-ijp-box:nth-child(4):last-child{grid-column:1/-1}
/* column key (the source table's own headers) */
.as-legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:18px 0 -8px;font-size:11.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#6a6a70}
.as-legend span+span::before{content:"";display:inline-block;width:5px;height:5px;margin-right:14px;border-radius:50%;background:#a8812b;vertical-align:middle}
/* ── step timeline ── */
.as-steps{list-style:none;margin:22px 0;padding:0;counter-reset:none}
.as-steps>li{position:relative;display:grid;grid-template-columns:46px minmax(0,1fr);column-gap:18px;padding-bottom:16px}
.as-steps>li::before{content:"";position:absolute;left:22px;top:46px;bottom:-2px;width:2px;background:repeating-linear-gradient(#b9b9bf 0 6px,transparent 6px 11px)}
.as-steps>li:last-child::before{display:none}
.as-st-n{width:46px;height:46px;border-radius:50%;background:#151515;color:#fff;display:grid;place-items:center;font-weight:800;font-size:17px;box-shadow:0 0 0 4px #fff,0 0 0 6px #a8812b;font-variant-numeric:tabular-nums}
.as-st-n.is-dot{background:#fff;box-shadow:0 0 0 2px #151515}
.as-st-n.is-dot::after{content:"";width:14px;height:14px;border-radius:50%;background:#151515}
.as-st-c{background:#fff;border:1px solid rgba(0,0,0,.1);border-radius:16px;padding:14px 20px 16px;box-shadow:0 1px 0 rgba(0,0,0,.04)}
.as-st-t{margin:0;font-size:17.5px;font-weight:700;line-height:1.3}
.as-st-d{display:inline-block;margin:0 0 8px;padding:3px 12px;border-radius:999px;background:#151515;color:#fff;font-size:13px;font-weight:700}
.as-st-b{margin:8px 0 0;font-size:15.5px;line-height:1.6}
.as-st-k{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.as-st-k span{display:inline-flex;gap:7px;align-items:baseline;padding:5px 12px;border-radius:999px;background:#f0f0f2;border:1px solid rgba(0,0,0,.08);font-size:13.5px;font-weight:600}
.as-st-k i{font-style:normal;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#6a6a70;font-weight:700}
/* ── meters ── */
td.as-m .as-meter{display:inline-flex;gap:3px;margin-right:9px;vertical-align:middle}
td.as-m .as-meter i{width:9px;height:14px;border-radius:3px;background:#d3d3d8}
td.as-m .as-meter[data-v="1"] i:nth-child(-n+1),td.as-m .as-meter[data-v="2"] i:nth-child(-n+2),td.as-m .as-meter[data-v="3"] i:nth-child(-n+3){background:#151515}
/* ── rating grades ── */
.as-gr{display:inline-grid;place-items:center;min-width:36px;height:36px;padding:0 8px;border-radius:10px;background:#151515;color:#fff;font-weight:800;font-size:16px}
.as-gr.is-r{border-radius:50%;background:#fff;color:#151515;box-shadow:inset 0 0 0 2px #151515}
tr[style*="--lv"] td:first-child{border-left:5px solid rgba(21,21,21,calc(var(--lv)*.18))}
/* ── stat tiles ── */
.as-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:20px 0}
.as-tile{background:#fff;border:1px solid rgba(0,0,0,.1);border-top:4px solid #151515;border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;gap:6px}
.as-t-l{font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6a6a70}
.as-t-v{font-size:clamp(22px,2.1vw,29px);font-weight:800;letter-spacing:-.02em;line-height:1.15}
.as-t-v .v7-key{background:none!important;box-shadow:none!important;padding:0!important}
.as-t-n{font-size:14.5px;line-height:1.5}
/* ── career ladder ── */
.as-ladder{display:grid;gap:14px;margin:22px 0}
.as-lad{background:#fff;border:1px solid rgba(0,0,0,.1);border-radius:16px;padding:16px 18px}
.as-lad-h{margin:0 0 12px;font-size:17px;font-weight:800}
.as-lad-r{display:flex;flex-wrap:wrap;gap:10px 34px}
.as-lad-s{position:relative;flex:1 1 170px;min-width:0;padding:10px 14px;border-radius:12px;background:#f0f0f2;border:1px solid rgba(0,0,0,.08);font-size:14.5px;font-weight:600;line-height:1.4}
.as-lad-s[data-k="2"]{background:#e3e3e6}.as-lad-s[data-k="3"]{background:#c9c9ce}.as-lad-s[data-k="4"]{background:#151515;color:#fff}
.as-lad-s i{display:block;margin-bottom:4px;font-style:normal;font-size:11px;letter-spacing:.09em;text-transform:uppercase;font-weight:700;opacity:.65}
.as-lad-s+.as-lad-s::before{content:"";position:absolute;left:-27px;top:50%;width:20px;height:2px;background:#151515;transform:translateY(-50%)}
.as-lad-s+.as-lad-s::after{content:"";position:absolute;left:-12px;top:50%;border:5px solid transparent;border-left:7px solid #151515;transform:translateY(-50%)}
/* ── pair cards ── */
.as-pairs{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;margin:20px 0}
.as-pair{background:#fff;border:1px solid rgba(0,0,0,.1);border-radius:16px;padding:16px 18px 16px 58px;position:relative}
.as-pair::before{content:"";position:absolute;left:16px;top:16px;width:28px;height:28px;border-radius:9px;background:#151515}
.as-pair::after{content:"";position:absolute;left:26px;top:22px;width:10px;height:6px;border-left:2.5px solid #fff;border-bottom:2.5px solid #fff;transform:rotate(-45deg)}
.as-pair h4{margin:0 0 6px;font-size:16.5px;font-weight:700;line-height:1.3}
.as-pair p{margin:0;font-size:15px;line-height:1.55}
.as-pair p+p{margin-top:6px}
.as-pair .as-cap{display:block;font-size:11px;letter-spacing:.09em;text-transform:uppercase;font-weight:700;color:#6a6a70;margin-bottom:2px}
@media(max-width:860px){.as-ghost{font-size:72px;bottom:-60px}.as-steps>li{grid-template-columns:38px minmax(0,1fr);column-gap:12px}.as-st-n{width:38px;height:38px;font-size:15px}.as-steps>li::before{left:18px;top:38px}.as-lad-s+.as-lad-s::before,.as-lad-s+.as-lad-s::after{display:none}.as-lad-r{gap:10px}}
</style>'''

ICONS = {
    'bulb': '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    'dealer': '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4M10 10h4M10 14h4M10 18h4"/>',
    'cust': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
}

norm = lambda s: re.sub(r'\s+', ' ', s or '').strip()


def inner(tag):
    return ''.join(str(c) for c in tag.contents).strip()


def cells(tr):
    return tr.find_all(['th', 'td'], recursive=False)


def parse(frag):
    soup = BeautifulSoup(frag, 'html.parser')
    t = soup.find('table')
    rows = t.find_all('tr')
    hd = [norm(c.get_text(' ')) for c in cells(rows[0])]
    body = [cells(r) for r in rows[1:]]
    return soup, t, hd, body


# ─────────────── transforms ───────────────
def legend(hd):
    return '<div class="as-legend" aria-label="Columns of the source table">' + ''.join(f'<span>{h}</span>' for h in hd if h) + '</div>'


def steps(hd, body, dated=False):
    out = ['<ol class="as-steps">']
    for i, r in enumerate(body, 1):
        c0 = norm(r[0].get_text(' '))
        if dated:
            node, lead, rest = '<span class="as-st-n is-dot" aria-hidden="true"></span>', f'<span class="as-st-d">{inner(r[0])}</span>', r[1:]
            title, rest = inner(r[1]), r[2:]
            hh = hd[2:]
            body_html = ''
            card = lead + f'<h4 class="as-st-t">{title}</h4>'
        else:
            if re.fullmatch(r'\d+', c0):
                node = f'<span class="as-st-n" aria-hidden="true">{c0}</span>'
                title, rest, hh = inner(r[1]), r[2:], hd[2:]
            elif re.match(r'(?i)step\s*\d+', c0):
                node = '<span class="as-st-n is-dot" aria-hidden="true"></span>'
                title, rest, hh = inner(r[0]), r[1:], hd[1:]
            else:
                node = f'<span class="as-st-n" aria-hidden="true">{i}</span>'
                title, rest, hh = inner(r[0]), r[1:], hd[1:]
            card = f'<h4 class="as-st-t">{title}</h4>'
        chips = []
        for k, (c, h) in enumerate(zip(rest, hh)):
            t = norm(c.get_text(' '))
            if not t:
                continue
            if k == 0 and not dated and (len(t) > 70 or h.lower() in ('what happens', 'activity', 'what')):
                card += f'<p class="as-st-b">{inner(c)}</p>'
            elif len(t) > 70:
                card += f'<p class="as-st-b"><strong>{h}</strong> {inner(c)}</p>'
            else:
                chips.append(f'<span><i>{h}</i>{inner(c)}</span>')
        if chips:
            card += '<div class="as-st-k">' + ''.join(chips) + '</div>'
        out.append(f'<li>{node}<div class="as-st-c">{card}</div></li>')
    out.append('</ol>')
    return ''.join(out)


def tiles(hd, body):
    out = ['<div class="as-tiles">']
    for r in body:
        lab, val = inner(r[0]), inner(r[1])
        note = f'<span class="as-t-n">{inner(r[2])}</span>' if len(r) > 2 and norm(r[2].get_text()) else ''
        out.append(f'<div class="as-tile"><span class="as-t-l">{lab}</span><b class="as-t-v">{val}</b>{note}</div>')
    out.append('</div>')
    return ''.join(out)


def ladder(hd, body):
    out = ['<div class="as-ladder">']
    for r in body:
        steps_ = ''.join(f'<div class="as-lad-s" data-k="{k}"><i>{h}</i>{inner(c)}</div>' for k, (c, h) in enumerate(zip(r[1:], hd[1:]), 1) if norm(c.get_text(' ')))
        out.append(f'<div class="as-lad"><h4 class="as-lad-h">{inner(r[0])}</h4><div class="as-lad-r">{steps_}</div></div>')
    out.append('</div>')
    return ''.join(out)


def pairs(hd, body, caps=False):
    out = ['<div class="as-pairs">']
    for r in body:
        card = f'<h4>{inner(r[0])}</h4>'
        for c, h in zip(r[1:], hd[1:]):
            if norm(c.get_text(' ')):
                card += f'<p>{"<span class=as-cap>" + h + "</span>" if caps else ""}{inner(c)}</p>'
        out.append(f'<div class="as-pair">{card}</div>')
    out.append('</div>')
    return ''.join(out)


METER = {'low': 1, 'moderate': 2, 'medium': 2, 'high': 3, 'slow': 1, 'fast': 3}


def meters(soup, t, hd):
    cols = [i for i, h in enumerate(hd) if h in ('Cost', 'Speed of hiring', 'Candidate quality')]
    n = 0
    for tr in t.find_all('tr')[1:]:
        cs = cells(tr)
        for i in cols:
            if i < len(cs):
                v = METER.get(norm(cs[i].get_text()).lower())
                if v:
                    cs[i]['class'] = cs[i].get('class', []) + ['as-m']
                    m = BeautifulSoup(f'<span class="as-meter" data-v="{v}" aria-hidden="true"><i></i><i></i><i></i></span>', 'html.parser')
                    cs[i].insert(0, m)
                    n += 1
    return n


def grades(soup, t, hd):
    for tr in t.find_all('tr')[1:]:
        cs = cells(tr)
        if re.fullmatch(r'[1-5]', norm(cs[0].get_text())):
            tr['style'] = f'--lv:{norm(cs[0].get_text())}'
        for i, cls in ((0, 'as-gr is-r'), (1, 'as-gr')):
            if norm(cs[i].get_text()):
                w = soup.new_string('')
                span = soup.new_tag('span', attrs={'class': cls})
                span.extend(list(cs[i].contents))
                cs[i].clear()
                cs[i].append(span)


def words(s):
    return re.sub(r'<[^>]+>', ' ', s)


def table_pass(reg):
    stats = {}

    def one(m):
        frag = m.group(0)
        if 'as-tg' in m.group(1) or 'as-ig-done' in frag:
            return frag
        soup, t, hd, body = parse(frag)
        if not body or any(len(r) != len(hd) for r in body):
            return frag
        lens = max((len(norm(c.get_text(' '))) for r in body for c in r), default=0)
        h0 = hd[0].lower()
        new = None
        kind = None
        if h0 in ('step', 'step #') and len(hd) >= 3:
            above = re.sub(r'<[^>]+>', ' ', reg[max(0, m.start() - 4000):m.start()])
            titles = [norm(r[1].get_text(' ')) for r in body if re.fullmatch(r'\d+', norm(r[0].get_text()))]
            if titles and sum(1 for t in titles if t and t in above) >= max(2, round(len(titles) * 0.6)):
                return frag  # the same stages are already drawn as a chart right above
            new, kind = steps(hd, body), 'steps'
        elif h0.startswith('date') and len(hd) >= 3:
            new, kind = steps(hd, body, dated=True), 'dated'
        elif hd == ['Stage', 'Notice Period']:
            new, kind = tiles(hd, body), 'tiles'
        elif hd == ['Type', 'How many days', 'For what'] and max(len(norm(r[1].get_text(' '))) for r in body) <= 26:
            new, kind = tiles(hd, body), 'tiles'
        elif hd[0] == 'Work Area' and len(hd) == 5:
            new, kind = ladder(hd, body), 'ladder'
        elif hd in (['Outcome', 'When', 'What follows'], ['Level', 'Meaning', 'Action']):
            new, kind = pairs(hd, body, caps=True), 'cards'
        elif hd in (['Factor', 'What to check'], ['Check', 'Document and method'], ['Part', 'What it includes'], ['Situation', 'What happens'],
                    ['Item', 'Quantity'], ['Eligibility', 'How it is checked'], ['Move', 'Why it often works'], ['Item', 'Recommended'],
                    ['Question', 'Answer']):
            new, kind = pairs(hd, body), 'pairs'
        elif 'Candidate quality' in hd:
            n = meters(soup, t, hd)
            new, kind = str(soup), 'meters' if n else None
        elif hd[:2] == ['Rating', 'Grade']:
            grades(soup, t, hd)
            new, kind = str(soup), 'grades'
        if not new:
            return frag
        # no word may be added: every text node of the result must come from the original table's cells or headers
        src = {norm(x) for x in BeautifulSoup(frag, 'html.parser').stripped_strings}
        src_all = norm(' '.join(BeautifulSoup(frag, 'html.parser').stripped_strings))
        for s in BeautifulSoup(new, 'html.parser').stripped_strings:
            s = norm(s)
            assert s in src or s in src_all or re.fullmatch(r'\d{1,2}', s), (kind, hd, s)
        stats[kind] = stats.get(kind, 0) + 1
        if kind in ('meters', 'grades'):
            return new
        return f'<div class="as-ig-done">{legend(hd)}{new}</div>'

    reg = re.sub(r'<div class="table-wrap([^"]*)">\s*<table>.*?</table>\s*</div>', one, reg, flags=re.S)
    return reg, stats


# ─────────────── openers ───────────────
def opener_pass(reg):
    n = 0

    def head(m):
        nonlocal n
        art_id, kicker_num = m.group(1), m.group(2)
        n += 1
        return m.group(0).replace('<div class="jx-head-row">', f'<div class="jx-head-row"><span class="as-ghost" aria-hidden="true">{int(kicker_num):02d}</span>', 1)

    reg = re.sub(r'<article class="jx-chapter" id="chap-(ch\d+)" hidden>\s*<header class="jx-head"><div class="jx-head-row"><div><p class="jx-kicker">CHAPTER (\d+)</p>', head, reg)
    # section chips
    def secs(m):
        body = m.group(0)
        art_id = m.group(1)
        subs = re.findall(rf'<h3 class="sub-title subhead" id="({art_id}-\d+)">(\d+\.\d+)\s+([^<]+)</h3>', body)
        if len(subs) < 2:
            return body
        chips = ''.join(f'<a href="#{i}"><b>{num}</b><span>{t.strip()}</span></a>' for i, num, t in subs)
        return body.replace('</header>', f'</header>\n<nav class="as-secs" aria-label="Sections">{chips}</nav>', 1)
    reg = re.sub(r'<article class="jx-chapter" id="chap-(ch\d+)".*?</article>', secs, reg, flags=re.S)

    def ico(m):
        t = m.group(2).strip().lower()
        k = 'bulb' if t.startswith(('objective', 'purpose')) else 'dealer' if 'dealer' in t else 'cust' if 'customer' in t else None
        if not k:
            return m.group(0)
        return f'{m.group(1)}<svg class="as-ico" viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg><span>{m.group(2)}</span></span>'
    reg = re.sub(r'(<span class="eyebrow">)([^<]+)</span>', ico, reg)
    return reg, n


def routes_pass(reg):
    n = [0]

    def one(m):
        soup, t, hd, body = parse(m.group(0))
        assert hd[0] == 'Work Area' and all(len(r) == len(hd) for r in body)
        new = legend(hd) + ladder(hd, body)
        src = ' '.join(BeautifulSoup(m.group(0), 'html.parser').stripped_strings)
        for s_ in BeautifulSoup(new, 'html.parser').stripped_strings:
            assert norm(s_) in src, s_
        n[0] += 1
        return new
    reg = re.sub(r'<div class="career-routes-matrix"[^>]*>\s*<table class="routes-table".*?</table>\s*</div>', one, reg, flags=re.S)
    return reg, n[0]


def run(reg):
    reg, nr = routes_pass(reg)
    print('ig2 routes ladder', nr)
    reg, st = table_pass(reg)
    reg, n = opener_pass(reg)
    print('ig2', st, 'headers', n)
    return reg
