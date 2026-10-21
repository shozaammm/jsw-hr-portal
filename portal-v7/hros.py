"""Rebrand to HROS (no TRUST) and lay chapter Principles out as an infographic. Idempotent; run on v2.html."""
import re, sys
P = sys.argv[1] if len(sys.argv) > 1 else 'v2.html'
h = open(P, encoding='utf-8').read()

# --- brand: sidebar, hero banner, footer
h = h.replace('<span>HR Operations Manual</span>', '<span>HROS</span>')
h = re.sub(r'<span class="jx-hero-word" aria-label="TRUST">.*?</span></span>\s*<span class="jx-hero-line">JSW HR Operations Manual</span>',
           '<span class="jx-hero-word" aria-label="HROS">' + ''.join(f'<span aria-hidden="true" style="--i:{i}">{c}</span>' for i, c in enumerate('HROS')) + '</span>\n          <span class="jx-hero-line">Human Resource Operating System</span>',
           h, flags=re.S)
h = re.sub(r'\s*<ul class="jx-pillars">.*?</ul>', '', h, count=1, flags=re.S)
h = h.replace('<p>TRUST: JSW HR Operations Manual</p>', '<p>HROS: Human Resource Operating System</p>')

# --- principles infographic (first flat list after each Principles heading)
def cards(m):
    items = re.findall(r'<li>(.*?)</li>', m.group(2), re.S)
    c = ''.join(f'<li class="pr-card"><span class="pr-num">{i:02d}</span><p>{t.strip()}</p></li>' for i, t in enumerate(items, 1))
    return f'{m.group(1)}<ol class="pr-grid pr-n{len(items)}">{c}</ol>'
h = re.sub(r'(<h3 class="sub-title subhead">Principles</h3>\s*)<ul class="list-clean"[^>]*>((?:(?!</ul>).)*?)</ul>', cards, h, flags=re.S)

CSS = '''<style id="jx-principles">
.pr-grid{list-style:none;margin:14px 0 22px;padding:0;display:grid;gap:14px;grid-template-columns:repeat(3,1fr);counter-reset:none}
.pr-grid.pr-n2{grid-template-columns:repeat(2,1fr)}
.pr-card{position:relative;margin:0;padding:18px 18px 20px;border:1px solid rgba(0,0,0,.14);border-top:4px solid #151515;border-radius:12px;background:rgba(255,255,255,.72);overflow:hidden}
.pr-card::after{content:"";position:absolute;right:-26px;bottom:-26px;width:90px;height:90px;border-radius:50%;background:rgba(0,0,0,.05)}
.pr-num{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%;background:#151515;color:#fff;font-weight:700;font-size:14px;letter-spacing:.02em;margin-bottom:12px}
.pr-card p{margin:0;font-size:15px;line-height:1.45;font-weight:500;position:relative;z-index:1}
@media(max-width:800px){.pr-grid,.pr-grid.pr-n2{grid-template-columns:1fr}}
</style>
'''
if 'id="jx-principles"' not in h:
    h = h.replace('<style id="jx-mp">', CSS + '<style id="jx-mp">', 1)
open(P, 'w', encoding='utf-8').write(h)
print('ok')
