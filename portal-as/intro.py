"""Introduction pages: i Foreword, ii Vision and Foundation, iii HR Systems at a Glance."""
import html, re
import build as B

esc = lambda s: html.escape(s, quote=False)

LEVEL_RE = re.compile(r'^(Basic|Advance|Leader)\s*:\s*(.*)$')
ICO = {
    'People & Leadership': '<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.4"/><path d="M16.5 14.2A5 5 0 0 1 21 19"/>',
    'Systems & Processes': '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
    'Culture': '<path d="M12 21s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 11c0 5.6-7 10-7 10z"/>',
}


def cards(items, n_cls=''):
    """[(title, text)] -> numbered cards, in the portal's own pr-grid style."""
    li = ''.join(f'<li class="pr-card"><span class="pr-num">{i:02d}</span><p><strong>{esc(t)}</strong><br>{esc(x)}</p></li>'
                 for i, (t, x) in enumerate(items, 1))
    return f'<ol class="pr-grid{n_cls}">{li}</ol>'


def foreword(D, chunks):
    msg = []
    for n in (1, 2, 3):
        key = f'Foreword (Option {n})'
        r = B.Renderer(D, 'fm-i'); r.render(chunks[key]['blocks'])
        body = '\n'.join(r.out)
        sig = re.search(r'<p>\[Name\]</p>\s*<p>\[Designation\]</p>\s*<p>(JSW Motors)\s*</p>\s*$', body)
        assert sig, key
        body = body[:sig.start()] + ('<div class="signoff"><div class="sig-line"></div><div class="sig-name">[Name]</div>'
                                     '<div class="sig-role">[Designation]</div><div class="sig-org">JSW Motors</div></div>')
        head = f'<h3 class="sub-title subhead"{" style=\"margin-top:0\"" if n == 1 else ""}>{esc(key)}</h3>'
        msg.append(f'{head}\n{body}')
    return B.article('fm-i', 'i.', 'Foreword', '\n'.join(msg))


def vision(D, chunks):
    parts = []
    for name in ('JSW Group Vision and Foundation', 'JSW Motors Vision and Foundation'):
        label = name.replace(' Vision and Foundation', '')
        parts.append(f'<h3 class="sub-title subhead"{" style=\"margin-top:0\"" if "Group" in name else ""}>{esc(label)}</h3>')
        bl = chunks[name]['blocks']
        i, out = 0, []
        while i < len(bl):
            b = bl[i]
            if b['lvl'] == 2:
                out.append(f'<h4 class="item-title">{esc(b["text"])}</h4>'); i += 1; continue
            if b['lvl'] == 4:                       # a run of "value title + sentence" pairs -> cards
                items = []
                while i + 1 < len(bl) and bl[i]['lvl'] == 4:
                    items.append((bl[i]['text'], bl[i + 1]['text'])); i += 2
                out.append(cards(items, ' pr-n2' if len(items) == 4 else ''))
                continue
            out.append(f'<p>{b["html"]}</p>'); i += 1
        parts.append('\n'.join(out))
    return B.article('fm-ii', 'ii.', 'JSW Group and JSW Motors Vision and Foundation', '\n'.join(parts))


def glance(D, chunks):
    bl = [b for b in chunks['Contents']['blocks'] if b['k'] == 'p']
    t = [b['text'] for b in bl]
    assert t[0] == 'HR SYSTEMS AT A GLANCE'
    out = [f'<h3 class="sub-title subhead" style="margin-top:0">{esc(t[0].title().replace("Hr ", "HR ").replace(" At A ", " at a "))}</h3>',
           f'<h4 class="item-title">{esc(t[1])}</h4>', f'<p>{esc(t[2])}</p>']
    # three groups: bold list-paragraph heading followed by its bullets
    groups, cur = [], None
    for b in bl[3:]:
        if b['text'] == 'KEY HR GUIDELINES FOR DEALERS':
            break
        if b['text'] in ICO:
            cur = [b['text'], []]; groups.append(cur); continue
        # one source paragraph holds two bullets run together ("…promotion" + "Standardised induction…")
        for x in re.split(r'(?<=promotion)(?=Standardised )', b['text']):
            cur[1].append(x.strip())
    gh = []
    for name, items in groups:
        gh.append('<div class="ig-pr-card" role="listitem"><div class="ig-pr-head"><span class="ig-ico" aria-hidden="true">'
                  '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" '
                  f'stroke-linecap="round" stroke-linejoin="round">{ICO[name]}</svg></span><h4 class="ig-pr-title">{esc(name)}</h4></div>'
                  '<ul class="list-clean">' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul></div>')
    out.append('<div class="ig-pr" role="list">' + ''.join(gh) + '</div>')
    k = next(i for i, b in enumerate(bl) if b['text'] == 'KEY HR GUIDELINES FOR DEALERS')
    out.append(f'<h3 class="sub-title subhead">{esc(bl[k]["text"].title().replace("Hr ", "HR ").replace("For ", "for "))}</h3>')
    out.append(f'<p>{esc(bl[k + 1]["text"])}</p>')
    desc = {}
    for b in bl[k + 2:k + 5]:
        nm, _, tx = b['text'].partition('–')
        desc[nm.strip()] = tx.strip()
    lv = []
    for b in bl[k + 5:k + 8]:
        m = LEVEL_RE.match(b['text']); assert m, b['text']
        nm, rest = m.group(1), m.group(2)
        # "1.  Manpower planning & talent acquisition 2 Employee 3. Compensation & Rewards management"
        items = [(int(n), x.strip()) for n, x in re.findall(r'(?:(?<=\s)|^)(\d{1,2})\s*\.?\s+([A-Z][^\d]*?)(?=\s+\d{1,2}\s*\.?\s+[A-Z]|\s*$)', rest)]
        lv.append((nm, desc[nm], items))
    out.append('<div class="as-levels">' + ''.join(
        f'<div class="as-level as-level-{i}"><div class="as-level-h"><span class="as-level-n">{i}</span><h4>{esc(nm)}</h4></div>'
        f'<p class="as-level-d">{esc(d)}</p><ol class="as-level-l">' + ''.join(f'<li value="{n}">{esc(x)}</li>' for n, x in items) + '</ol></div>'
        for i, (nm, d, items) in enumerate(lv, 1)) + '</div>')
    return B.article('fm-iii', 'iii.', 'How to Read the Manual', '\n'.join(out))


def pages(D, chunks, ctx):
    return [foreword(D, chunks), vision(D, chunks), glance(D, chunks)]
