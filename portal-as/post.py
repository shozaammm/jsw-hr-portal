"""Whole-page post-processing for service.html (openers, Principles cards, emphasis, annexure chips, brand)."""
import re
import asdoc  # noqa
import build as B

AS_CSS = '''<style id="as-css2">
.as-ind{margin:18px 0}
.as-ind-root{background:#1b1b1d;color:#fff;border-radius:12px;padding:14px 18px;text-align:center;max-width:520px;margin:0 auto 16px}
.as-ind-root h4{margin:0;font-size:19px;color:#fff}
.as-ind-root p{margin:2px 0 0;font-size:13.5px;color:rgba(255,255,255,.78)}
.as-ind-cols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;align-items:start}
.as-ind-head{background:#e6e6e8;border:1.5px solid #8d8d92;border-radius:12px;padding:12px 14px;text-align:center;position:relative}
.as-ind-head h4{margin:0;font-size:17px}
.as-ind-head em{display:block;font-size:13.5px;color:#46474c}
.as-ind-head b{display:block;font-size:13.5px}
.as-ind-n{position:absolute;left:10px;top:10px;width:24px;height:24px;border-radius:50%;background:#1b1b1d;color:#fff;font-size:12px;font-weight:700;display:grid;place-items:center}
.as-ind-box{margin-top:10px;margin-left:14px;background:#fff;border:1.5px solid #b4b4b8;border-radius:10px;padding:10px 14px}
.as-ind-box h5{margin:0 0 6px;font-size:15px}
.as-ind-box ul{margin:0;padding-left:18px;font-size:13.5px;line-height:1.5}
@media(max-width:860px){.as-ind-cols{grid-template-columns:1fr}}
.as-levels{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:14px 0 8px}
.as-level{border:1px solid rgba(0,0,0,.14);border-top:4px solid #151515;border-radius:12px;background:rgba(255,255,255,.72);padding:16px 18px}
.as-level-h{display:flex;align-items:center;gap:10px}
.as-level-h h4{margin:0;font-size:18px}
.as-level-n{width:30px;height:30px;border-radius:50%;background:#151515;color:#fff;display:grid;place-items:center;font-weight:700;font-size:14px}
.as-level-d{font-size:14px;margin:10px 0 8px}
.as-level-l{margin:0;padding-left:0;list-style:none;display:grid;gap:6px}
.as-level-l li{font-size:14.5px;font-weight:600;padding:7px 10px;background:rgba(0,0,0,.05);border-radius:8px}
.as-level-l li::before{content:attr(value) ". ";font-variant-numeric:tabular-nums}
@media(max-width:860px){.as-levels{grid-template-columns:1fr}}
.as-note{font-size:14px;margin-top:10px}
.pr-grid.pr-n5{grid-template-columns:repeat(3,1fr)}
.rd-detail .chip{text-transform:none}
.fx-lj-body{text-align:left;display:flex;flex-direction:column;gap:8px}
.as-lj-when{font-weight:700;font-size:15px}
.as-lj-obj{font-size:13.5px;font-weight:500;line-height:1.5}
.as-theme{margin:6px 0 0;font-weight:700;font-size:14px}
.as-tg th,.as-tg td{text-align:center;vertical-align:middle}
.as-tg-r{background:#151515!important;color:#fff!important;width:90px}
.as-tg-c{font-weight:600}
.as-tg-0{background:#f1f1f2}.as-tg-1{background:#e1e1e4}.as-tg-2{background:#c9c9ce}.as-tg-3{background:#a9a9b0}.as-tg-4{background:#8b8b93;color:#fff}
.as-attr{margin:14px 0;display:grid;gap:12px}
.as-attr-f{display:flex;flex-wrap:wrap;gap:10px;align-items:center;background:#151515;color:#fff;border-radius:12px;padding:16px 20px;font-size:17px;font-weight:700}
.as-attr-f b{opacity:.7}
.as-attr-n{font-size:13.5px;margin:0}
.as-attr-e{border:1px solid rgba(0,0,0,.14);border-left:4px solid #151515;border-radius:12px;background:rgba(255,255,255,.72);padding:14px 18px}
.as-attr-e h5{margin:0 0 8px}
.as-attr-e ul{margin:0;padding-left:18px;line-height:1.7}
.as-attr-r{font-weight:700;font-size:1.05em;list-style:none;margin-left:-18px;margin-top:6px;padding:8px 12px;background:#151515;color:#fff;border-radius:8px}
</style>'''


def reorder(h):
    """Chapter openers: Objective/Purpose first, then the Benefit lists side by side, then Principles as its own sub-heading."""
    row_re = re.compile(r'<div class="meta-row reveal"[^>]*>')
    out, pos, n = [], 0, 0
    for m in row_re.finditer(h):
        if m.start() < pos:
            continue
        end = B._div_end(h, m.start())
        items = re.findall(r'<div class="meta-item">.*?</div>', h[m.end():end], re.S)
        purpose = [x for x in items if re.search(r'<span class="eyebrow">(Purpose|Objective):?\s*</span>', x, re.I)]
        pr = [x for x in items if re.search(r'<span class="eyebrow">Principles:?\s*</span>', x, re.I)]
        rest = [x for x in items if x not in pr and x not in purpose]
        if not purpose or 'data-solo' in m.group(0):
            continue
        solo = re.sub(r'style="', 'data-solo="1" style="', m.group(0), 1)
        if pr:
            body = re.sub(r'<div class="meta-item"><span class="eyebrow">Principles:?\s*</span>\s*(.*)</div>$', r'\1', pr[0].strip(), flags=re.S | re.I)
            princ = '\n<h3 class="sub-title subhead">Principles</h3>\n' + body
        else:
            princ = ''
        out.append(h[pos:m.start()] + solo + ''.join(purpose) + '</div>\n' + (m.group(0) + ''.join(rest) + '</div>' if rest else '') + princ + '\n')
        pos = end
        n += 1
    out.append(h[pos:])
    print('openers reordered', n)
    return ''.join(out)


def principle_cards(h):
    def cards(m):
        items = re.findall(r'<li>(.*?)</li>', m.group(2), re.S)
        c = ''.join(f'<li class="pr-card"><span class="pr-num">{i:02d}</span><p>{t.strip()}</p></li>' for i, t in enumerate(items, 1))
        return f'{m.group(1)}<ol class="pr-grid pr-n{len(items)}">{c}</ol>'
    return re.sub(r'(<h3 class="sub-title subhead">Principles</h3>\s*)<ul class="list-clean"[^>]*>((?:(?!</ul>).)*?)</ul>', cards, h, flags=re.S)


def region(h):
    a = h.find('    <article class="jx-chapter" id="chap-fm-i"')
    e = h.find('</article>', h.find('id="chap-annexure"')) + len('</article>')
    return a, e


def run(h):
    a, e = region(h)
    reg = reorder(h[a:e])
    reg = principle_cards(reg)
    import readability
    strip = lambda x: re.sub(r'<[^>]+>', '', x)
    r2, stats, leads = readability.emphasize(reg)
    assert strip(r2) == strip(reg), 'emphasis changed text'
    print('emphasis', stats)
    reg = r2
    # annexure chips -> the annexure entry
    codes = set(re.findall(r'id="annex-(\d{1,2}[A-Z])"', reg))
    used = set(re.findall(r'<span class="v7-ref">(\d{1,2}[A-Z])</span>', reg))
    print('annex chips', len(used), 'missing', sorted(used - codes))
    reg = re.sub(r'<span class="v7-ref">(\d{1,2}[A-Z])</span>',
                 lambda m: f'<a class="v7-ref" href="#annex-{m.group(1)}">{m.group(1)}</a>' if m.group(1) in codes else m.group(0), reg)
    h = h[:a] + reg + h[e:]
    h = h.replace('</head>', AS_CSS + '</head>', 1)
    return h
