#!/usr/bin/env python3
"""HROS for Service (After Sales) — builds service.html.

Shell (design, CSS, JS, home, search, org-chart engine, role-directory engine) = v2.html at HEAD.
Every chapter is regenerated from the four Service Word files in ~/Downloads/HR_OS_Chapters.
Wording is copied verbatim; infographics only re-lay words that are in the files
(paragraphs, tables, or the text printed in the files' own shapes / pictures).
"""
import base64, html, json, os, re, subprocess, sys, tempfile
from pathlib import Path

import asdoc as A
import build as B
import flowcharts as fc
import jd as JD
import service_data as S
from infographics import Templates, career_matrix, calendar as cal_ig

REPO = A.HERE.parent
OUT = Path(os.environ.get('AS_OUT', REPO / 'service.html'))
esc = lambda s: html.escape(s, quote=False)
escq = lambda s: html.escape(s, quote=True)

# ───────────────────────── docx → chunks ─────────────────────────
def chunks_of(docs):
    chunks, cur = {}, None
    for d in docs[:3]:
        for b in d.blocks:
            if b['k'] == 'p' and b['style'] == 'Heading 1':
                cur = chunks.setdefault(b['text'], {'title': b['text'], 'blocks': []}); continue
            if b['k'] == 'p' and re.match(r'^CHAPTER\s+\d+$', b['text']):
                continue
            if cur is not None:
                cur['blocks'].append(b)
    # chapter 13 lives in its own file: no Heading 1, structure carried by numbers
    bl = [b for b in docs[3].blocks if not (b['k'] == 'p' and b['text'].startswith('Chapter 13 –'))]
    bl = [b for b in bl if not (b['k'] == 'p' and re.match(r'^CHAPTER\s+13$', b['text']))]
    assert bl[0]['text'] == 'Leadership Practices', bl[0]['text']
    chunks['Leadership Practices'] = {'title': 'Leadership Practices', 'blocks': bl[1:]}
    return chunks


CH_MAP = [  # (docx H1, portal id, kicker, number)
    ('Recruitment and Selection', 'ch3', 'CHAPTER 3', '3'),
    ('Compensation, Benefits and Incentive Policy', 'ch4', 'CHAPTER 4', '4'),
    ('Joining and Confirmation', 'ch5', 'CHAPTER 5', '5'),
    ('Learning and Development', 'ch6', 'CHAPTER 6', '6'),
    ('Performance Management', 'ch7', 'CHAPTER 7', '7'),
    ('Career Progression', 'ch8', 'CHAPTER 8', '8'),
    ('Employee Engagement, Rewards and Recognition', 'ch9', 'CHAPTER 9', '9'),
    ('Discipline and Conduct', 'ch10', 'CHAPTER 10', '10'),
    ('Employee Exit Management', 'ch11', 'CHAPTER 11', '11'),
    ('Organisation Policies', 'ch12', 'CHAPTER 12', '12'),
    ('Leadership Practices', 'ch13', 'CHAPTER 13', '13'),
]


def article(cid, kicker, title, body):
    return B.article(cid, kicker, title, body)


# ───────────────────────── renderer hooks ─────────────────────────
def make_hooks(T, ctx):
    import hooks
    return hooks.make(T, ctx)


def build():
    tmp = tempfile.mkdtemp(prefix='as-')
    docs = A.load_all(tmp)
    D = docs[0]
    chunks = chunks_of(docs)
    base_html = subprocess.run(['git', 'show', f'{B.BASE_COMMIT}:v2.html'], cwd=REPO, capture_output=True, text=True, check=True).stdout
    T = Templates(base_html)
    head = subprocess.run(['git', 'show', 'HEAD:v2.html'], cwd=REPO, capture_output=True, text=True, check=True).stdout
    import hooks
    B.META = re.compile(r'^:?\s*(Objective|Purpose|Principles|Benefits?\s+(?:for|to)\s+(?:the\s+)?(?:Dealers?|Dealerships?|Customers?))\s*:?\s*$', re.I)
    B.annex_html = S.annex_item
    ctx = {'D': D, 'docs': docs, 'chunks': chunks, 'T': T}
    B.Renderer.hooks = hooks.make(T, ctx)
    toc_subs, annex_all = {}, []

    # ── intro pages ─────────────────────────────────────────────
    import intro
    fm = intro.pages(D, chunks, ctx)
    # ── chapters 1 (org) / 2 (JD) ───────────────────────────────
    import chapters12
    ch2_html, ch1_html, subs12 = chapters12.build(D, chunks, docs, head)
    toc_subs.update(subs12)
    # ── chapters 3-13 ───────────────────────────────────────────
    arts = []
    for title, cid, kicker, n in CH_MAP:
        r = B.Renderer(D, cid)
        body = r.render(hooks.normalize(chunks[title]['blocks']))
        arts.append(article(cid, kicker, title, body))
        toc_subs[cid] = r.subs
        annex_all.append((n, title, r.annex))
    # ── annexure page ───────────────────────────────────────────
    annex_all = [('2', 'Job Descriptions', chapters12.JD_ANNEX)] + annex_all
    ab = []
    for n, title, items in annex_all:
        if not items:
            continue
        ab.append(f'<h3 class="sub-title subhead" id="annex-{n}">{esc(n + ". " + title)}</h3>')
        ab.append('<div class="annex-file-list as-annex">' + '\n'.join(S.annex_item(c, t) for c, t in items) + '</div>')
    annex_art = article('annexure', 'ANNEXURE', 'Annexures', '\n'.join(ab))

    # ── splice into the v2 shell ────────────────────────────────
    a = head.find('    <article class="jx-chapter" id="chap-fm-iii"')
    e = head.find('</article>', head.find('id="chap-compliances"')) + len('</article>')
    assert 0 < a < e
    region = '    ' + '\n    '.join(fm + [ch2_html, ch1_html] + arts + [annex_art])
    h = head[:a] + region + head[e:]
    h = S.patch_shell(h, toc_subs)
    import post
    h = post.run(h)
    OUT.write_text(h)
    print('wrote', OUT, len(h))


if __name__ == '__main__':
    build()
