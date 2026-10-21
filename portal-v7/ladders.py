"""Re-lays two V9 tables as designs: ch5 probation outcomes -> cards, ch8 career routes -> ladder.
Text is carried over unchanged; run on v2.html (idempotent)."""
import re, sys
P = sys.argv[1] if len(sys.argv) > 1 else 'v2.html'
h = open(P, encoding='utf-8').read()

CSS = '''<style id="jx-ladder">
.oc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:14px 0}
.oc-card{border:1px solid rgba(0,0,0,.14);border-top:4px solid var(--c,#151515);border-radius:12px;padding:18px 20px;background:rgba(255,255,255,.7)}
.oc-card h5{margin:0 0 12px;font-size:18px;display:flex;align-items:center;gap:10px}
.oc-card h5 i{width:12px;height:12px;border-radius:50%;background:var(--c);display:inline-block}
.oc-lbl{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.6;margin:12px 0 3px}
.oc-card p{margin:0}
.lad{margin:14px 0;overflow-x:auto}
.lad-in{min-width:760px}
.lad-head,.lad-row{display:grid;grid-template-columns:120px repeat(5,1fr);gap:8px}
.lad-head span{background:#151515;color:#fff;border-radius:6px;padding:8px 6px;text-align:center;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
.lad-head span:first-child{background:none}
.lad-row{margin-top:10px;padding:8px 0;border-top:1px solid rgba(0,0,0,.1);align-items:end;min-height:150px}
.lad-area{align-self:center;font-weight:700;font-size:13px}
.lad-step{position:relative;border-radius:8px;padding:10px 8px;text-align:center;font-weight:600;font-size:12px;background:#E9E9E9;border-bottom:4px solid #151515;display:flex;align-items:center;justify-content:center;line-height:1.25}
.lad-step.s1{height:44px}.lad-step.s2{height:62px;background:#E2E2E2}.lad-step.s3{height:80px;background:#D8D8D8}.lad-step.s4{height:98px;background:#CCC}.lad-step.s5{height:116px;background:#151515;color:#fff}
.lad-none{height:44px;text-align:center;opacity:.35;align-self:end}
@media(max-width:800px){.oc-grid{grid-template-columns:1fr}}
</style>
'''

# ---- ch5 outcomes
m = re.search(r'<div class="table-wrap"><table><thead><tr><th><strong>Outcome</strong></th>.*?</table></div>', h, re.S)
if m:
    rows = re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>', m.group(0), re.S)
    cols = ['#151515', '#6E6F74', '#B5B5B8']
    cards = ''.join(f'<div class="oc-card" style="--c:{c}"><h5><i></i>{o}</h5><div class="oc-lbl">When</div><p>{w}</p><div class="oc-lbl">What follows</div><p>{f}</p></div>'
                    for (o, w, f), c in zip(rows, cols))
    h = h.replace(m.group(0), f'<div class="oc-grid">{cards}</div>')

# ---- ch8 career routes
m = re.search(r'<figure class="img-card"><div class="career-routes-matrix".*?</table></div>', h, re.S)
if m:
    blk = m.group(0)
    heads = [' '.join(re.sub(r'<br\s*/?>', ' ', x).split()) for x in re.findall(r'<th(?:\s[^>]*)?>(.*?)</th>', blk, re.S)]
    out = '<figure class="img-card"><div class="lad"><div class="lad-in"><div class="lad-head">' + ''.join(f'<span>{x}</span>' for x in heads) + '</div>'
    for tr in re.findall(r'<tbody>(.*?)</tbody>', blk, re.S)[0].split('</tr>')[:-1]:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
        out += f'<div class="lad-row"><div class="lad-area">{cells[0]}</div>'
        for i, c in enumerate(cells[1:], 1):
            out += f'<div class="lad-step s{i}">{c}</div>' if c.strip() != '—' else '<div class="lad-none">—</div>'
        out += '</div>'
    out += '</div></div>'
    h = h.replace(blk + '', out)

if 'id="jx-ladder"' not in h:
    h = h.replace('<style id="jx-mp">', CSS + '<style id="jx-mp">', 1)
open(P, 'w', encoding='utf-8').write(h)
print('ok')

# ---- ch9 award tables: fit width, no sideways scroll
h = open(P, encoding='utf-8').read()
for first in ('<th><strong>Award</strong></th><th><strong>Description</strong></th><th><strong>Applicable for roles</strong></th>',
              '<th><strong>Award</strong></th><th><strong>Description</strong></th><th><strong>Roleholders</strong></th>'):
    h = h.replace('<div class="table-wrap"><table><thead><tr>' + first,
                  '<div class="table-wrap tw-fit"><table><thead><tr>' + first)
FIT = '''<style id="jx-fit">
.table-wrap.tw-fit{overflow-x:visible}
.table-wrap.tw-fit table{min-width:0;table-layout:fixed;width:100%}
.table-wrap.tw-fit *{white-space:normal !important}
.table-wrap.tw-fit th,.table-wrap.tw-fit td{font-size:12.5px;padding:10px 8px;overflow-wrap:anywhere;word-break:normal;vertical-align:top;white-space:normal !important;min-width:0 !important}
</style>
'''
if 'id="jx-fit"' not in h:
    h = h.replace('<style id="jx-mp">', FIT + '<style id="jx-mp">', 1)
open(P, 'w', encoding='utf-8').write(h)
