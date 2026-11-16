"""2026-11-16: 5A / 11B 'INITIATOR DETAILS' block: label sat in a 3%-wide column (wrapped letter-by-letter).
Merge cells (colspan only, no text change) so the box aligns with the table below. Rerunnable."""
import json, re
from pathlib import Path
from bs4 import BeautifulSoup
V2 = Path(__file__).resolve().parent.parent / 'v2.html'
h = V2.read_text(encoding='utf-8')
m = re.search(r'<script id="jx-annex-docs">window\.ANNEX_DOCS = (\{.*?\});</script>', h, re.S)
docs = json.loads(m.group(1).replace('<\\/', '</'))
def rb(s): return re.search(r'border-right:[^;"]*', s or '').group(0)
for k, lab in (('5A', 2), ('11B', 3)):
    s = BeautifulSoup(docs[k]['content'], 'html.parser')
    t = s.find('table'); n = int(t['data-cols']); rows = t.find_all('tr')
    before = re.sub(r'\s+', '', s.get_text())
    for i, r in enumerate(rows[:6]):
        tds = r.find_all('td')
        txt = tds[0].get_text(strip=True)
        if k == '5A':
            if i == 0:
                tds[0]['colspan'] = n
                for c in tds[1:]: c.decompose()
        else:
            if i in (0, 5):
                last = tds[-1]
                tds[0]['colspan'] = n
                tds[0]['style'] = re.sub(r'border-right:[^;"]*', rb(last['style']), tds[0]['style'])
                for c in tds[1:]: c.decompose()
            else:
                tds[0]['colspan'] = lab
                for c in tds[1:-1]: c.decompose()
                tds[-1]['colspan'] = n - lab
    assert re.sub(r'\s+', '', s.get_text()) == before
    docs[k]['content'] = str(s)
js = '<script id="jx-annex-docs">window.ANNEX_DOCS = ' + json.dumps(docs, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
V2.write_text(h[:m.start()] + js + h[m.end():], encoding='utf-8')
