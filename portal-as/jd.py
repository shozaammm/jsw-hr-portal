"""Parse the 30 Service job descriptions in chapter 2 of the docx into dicts."""
import re
import asdoc  # noqa  (puts portal-v7 on sys.path)
import build as B

SEC = re.compile(r'^([1-5])\.\s*(.+)$')
SUB = re.compile(r'^([A-Z])\.\s*(.+)$')
BUL = re.compile(r'^[•·▪\-–]\s*')


def region(D):
    s = next(i for i, b in enumerate(D.blocks) if b['k'] == 'p' and b['style'] == 'Heading 1' and b['text'] == 'Job Descriptions')
    e = next(i for i, b in enumerate(D.blocks) if i > s and b['k'] == 'p' and b['text'].startswith('ANNEXTURE'))
    return D.blocks[s + 1:e]


def parse(D):
    blocks = region(D)
    # role titles: the paragraph right before a table whose first cell is "Department"
    starts = []
    for i, b in enumerate(blocks):
        if b['k'] == 'tbl' and b['t'].rows[0].cells[0].text.strip() == 'Department':
            j = i - 1
            while j >= 0 and blocks[j]['k'] != 'p':
                j -= 1
            starts.append((j, i))
    roles, notes = [], []
    pre = blocks[:starts[0][0]]
    notes += [('before first role', b['text']) for b in pre if b['k'] == 'p']
    for n, (ti, tbi) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(blocks)
        title = blocks[ti]['text'].strip()
        meta = []
        for r in blocks[tbi]['t'].rows:
            cs = B.cells_of(r)
            meta.append((cs[0].text.strip(), cs[1].text.strip() if len(cs) > 1 else ''))
        role = {'title': title, 'meta': meta, 'overview': [], 'sections': []}
        cur = None          # current numbered section
        sub = None
        for b in blocks[tbi + 1:end]:
            if b['k'] == 'tbl':
                if any(c.text.strip() for r in b['t'].rows for c in r.cells):
                    notes.append((title, 'NON-EMPTY TABLE ' + ' | '.join(c.text.strip() for r in b['t'].rows for c in r.cells)))
                continue
            t = BUL.sub('', b['text'].strip())
            if not t:
                continue
            bold = b['bold']
            if bold and t == 'Position Overview':
                cur = {'name': 'Position Overview', 'items': [], 'groups': []}
                role['sections'].append(cur); sub = None
                continue
            m = SEC.match(t)
            if bold and m:
                cur = {'num': m.group(1), 'name': t, 'items': [], 'groups': []}
                role['sections'].append(cur); sub = None
                continue
            if cur is None:
                notes.append((title, 'LINE BEFORE FIRST SECTION: ' + t)); continue
            if bold:                                    # group label inside the section (A. … / Business Performance)
                sub = {'name': t, 'items': []}
                cur['groups'].append(sub)
                continue
            (sub['items'] if sub is not None else cur['items']).append(t)
        roles.append(role)
    return roles, notes


if __name__ == '__main__':
    import tempfile, asdoc as A
    docs = A.load_all(tempfile.mkdtemp())
    roles, notes = parse(docs[0])
    print(len(roles), 'roles')
    for r in roles:
        print(r['title'], '|', [(s['name'][:22], len(s['items']), [(g['name'][:18], len(g['items'])) for g in s['groups']]) for s in r['sections']])
    print('NOTES'); [print(n) for n in notes]
