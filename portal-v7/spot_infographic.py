"""Chapter 9.2 'Spot Recognition' infographic restyled as die-cut recognition tags (white sticker border, bold
yellow / mustard / blue cards with an icon), after the dealership's physical recognition tags.
Text is unchanged (SPOT, 01-03 and their lines). Rerunnable, applied to v2.html.

usage: python3 portal-v7/spot_infographic.py
"""
import re
from pathlib import Path

V2 = Path(__file__).resolve().parent.parent / 'v2.html'
h = V2.read_text(encoding='utf-8')

a = h.index('<figure class="fx-fig fx-spot')
b = h.index('</figure>', a) + len('</figure>')
old = h[a:b]
texts = re.findall(r'<p class="fx-text">(.*?)</p>', old)
assert texts == ['first booking by a new joiner', 'large fleet sales or bulk deal', 'high-value referrals'], texts

SMILE = ('<svg class="sp-smile" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
         '<circle cx="50" cy="50" r="47" fill="#FFE04D" stroke="#fff" stroke-width="6"/>'
         '<ellipse cx="35" cy="40" rx="5.500" ry="8" fill="#1b1b1d"/><ellipse cx="65" cy="40" rx="5.500" ry="8" fill="#1b1b1d"/>'
         '<path d="M26 58 Q50 84 74 58" fill="none" stroke="#1b1b1d" stroke-width="5" stroke-linecap="round"/></svg>')
ICONS = [
    # thumbs up
    '<svg class="sp-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>',
    # light bulb with rays
    '<svg class="sp-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 17.500h6M10 20.500h4"/><path d="M8.500 15c-1.500-1.200-2.500-3-2.500-5a6 6 0 1 1 12 0c0 2-1 3.800-2.500 5z"/><path d="M12 1.200v1.300M3.300 4.800l.9.9M20.700 4.800l-.9.9M1.200 10h1.300M21.500 10h1.300"/></g></svg>',
    # star
    '<svg class="sp-ico" viewBox="0 0 60 58" aria-hidden="true" focusable="false"><path d="M30 3l8.200 17 18.600 2.400-13.700 12.800 3.500 18.400L30 44.500 13.400 53.600l3.500-18.400L3.200 22.400 21.800 20z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
]
nodes = ''.join(
    f'<div class="fx-node sp-tag sp-t{i + 1}"><span class="fx-badge">0{i + 1}</span>{ICONS[i]}<p class="fx-text">{t}</p></div>'
    for i, t in enumerate(texts))
new = (f'<figure class="fx-fig fx-spot sp-die"><div class="fx-spot-hub">{SMILE}<span>SPOT</span></div>'
       f'<div class="fx-spot-row" style="--n:3">{nodes}</div></figure>')
h = h[:a] + new + h[b:]

CSS = '''<style id="jx-spot-info-css">
.jx-chapter .sp-die .fx-spot-hub{background:#F9C80E;color:#1b1b1d;border:5px solid #fff;padding:6px 28px 6px 10px;gap:10px;font-size:22px;font-weight:900;font-style:italic;letter-spacing:.02em;box-shadow:0 0 0 1px rgba(0,0,0,.14),0 8px 18px rgba(0,0,0,.2)}
.jx-chapter .sp-die .sp-smile{width:44px;height:44px;flex:none;filter:drop-shadow(0 2px 3px rgba(0,0,0,.25))}
.jx-chapter .sp-die .fx-spot-row .sp-tag{align-items:center;text-align:center;gap:10px;padding:34px 18px 22px;border:6px solid #fff;border-radius:26px 26px 18px 18px;box-shadow:0 0 0 1px rgba(0,0,0,.14),0 10px 22px rgba(0,0,0,.2);background:var(--tg);color:var(--tx)}
.jx-chapter .sp-die .fx-spot-row .sp-tag::before{display:none}
.jx-chapter .sp-die .sp-t1{--tg:#F9C80E;--tx:#1b1b1d;--ic:#1b1b1d}
.jx-chapter .sp-die .sp-t2{--tg:#F2B544;--tx:#7A1F3D;--ic:#7A1F3D}
.jx-chapter .sp-die .sp-t3{--tg:#2F6FD0;--tx:#fff;--ic:#F28C28}
.jx-chapter .sp-die .sp-tag .sp-ico{width:46px;height:46px;color:var(--ic);flex:none}
.jx-chapter .sp-die .sp-tag p.fx-text{color:var(--tx);font-size:16.5px;line-height:1.3;font-weight:800;font-style:italic;text-transform:uppercase;letter-spacing:.01em}
.jx-chapter .sp-die .sp-tag .fx-badge{left:50%;top:-22px;margin-left:-17px;background:#1E2A4A;box-shadow:0 0 0 3px #fff}
.jx-chapter .sp-die .fx-spot-row .sp-tag::after{top:-34px;height:34px}
@media (max-width:760px){.jx-chapter .sp-die .fx-spot-row{gap:38px}}
</style>'''
if 'id="jx-spot-info-css"' in h:
    h = re.sub(r'<style id="jx-spot-info-css">.*?</style>', lambda _: CSS, h, count=1, flags=re.S)
else:
    h = h.replace('<style id="jx-annex-docs-css">', CSS + '<style id="jx-annex-docs-css">', 1)
V2.write_text(h, encoding='utf-8')
print('spot infographic restyled')
