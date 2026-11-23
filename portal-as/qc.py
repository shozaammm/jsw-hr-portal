#!/usr/bin/env python3
"""Two-way QC: (1) every docx text unit appears in service.html; (2) every page text node is in the docx (or is a known UI label)."""
import re, sys, tempfile, html as H
from pathlib import Path
import asdoc as A
from bs4 import BeautifulSoup

PAGE = Path(sys.argv[1] if len(sys.argv) > 1 else A.HERE.parent / 'service.html')
norm = lambda s: re.sub(r'[\s ​]+', ' ', re.sub(r'[-•·▪]', ' ', s)).strip().lower().replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
squash = lambda s: re.sub(r'[^a-z0-9]', '', norm(s))


def docx_units(tmp):
    units = []
    for i in (1, 2, 3, 4):
        import docx
        d = docx.Document(A.accepted(i, tmp))
        body = d.element.body
        W = A.NS['w']
        for p in body.iter('{%s}p' % W):
            t = ''
            for n in p.iter():
                if n.tag == '{%s}t' % W: t += n.text or ''
                elif n.tag == '{%s}br' % W: t += '\n'
                elif n.tag == '{%s}tab' % W: t += ' '
            for line in t.split('\n'):
                if line.strip():
                    units.append((i, line.strip()))
    return units


def page_text():
    s = PAGE.read_text(encoding='utf8')
    soup = BeautifulSoup(s, 'html.parser')
    for t in soup(['script', 'style', 'svg']):
        t.decompose()
    a = soup.find('article', id='chap-fm-i')
    arts = soup.find_all('article', class_='jx-chapter')
    return arts, soup


def main():
    tmp = tempfile.mkdtemp()
    units = docx_units(tmp)
    arts, soup = page_text()
    blob = ' '.join(a.get_text(' ') for a in arts)
    # rdStore / hidden stores are inside articles too
    sq = squash(blob)
    miss = []
    seen = set()
    for i, u in units:
        k = squash(u)
        if len(k) < 8 or k in seen:
            continue
        seen.add(k)
        if k not in sq:
            miss.append((i, u))
    print(f'docx units checked: {len(seen)}  missing from page: {len(miss)}')
    for i, u in miss:
        print(f'  [file{i}] {u[:170]}')


if __name__ == '__main__':
    main()


def reverse():
    """page text -> docx: every text block in the chapter articles must exist in the docx."""
    tmp = tempfile.mkdtemp()
    units = docx_units(tmp)
    sq = squash(' '.join(u for _, u in units))
    # shape texts are joined with spaces in 'units' already (they are w:t runs)
    arts, soup = page_text()
    bad = []
    for a in arts:
        for node in a.find_all(string=True):
            t = node.strip()
            if len(t) < 12:
                continue
            k = squash(t)
            if k not in sq:
                bad.append((a.get('id'), t))
    print(f'page text nodes not found in docx: {len(bad)}')
    for cid, t in bad[:150]:
        print(f'  [{cid}] {t[:150]}')


if len(sys.argv) > 2 and sys.argv[2] == 'rev':
    reverse()
