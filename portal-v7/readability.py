"""Reading emphasis for the manual's prose — markup only, never wording.

Every rule wraps existing characters in a span/strong; the text content of
every element is unchanged (build.py asserts this). Applied to text inside
<p>, <li> and <td> of the chapter articles, outside headings, links, existing
bold, and the interactive infographics.

  1. lead-in  : "Purpose – …", "RMS (…) – to drive …", "Note: …"  → <strong class="v7-lead">
  2. key fact : 30 days · 6 months · INR 2,500 · ≥60% · 45-60% · 20th  → <span class="v7-key">
  3. form ref : annexure 3E · 3E. Employee referral form            → <span class="v7-ref">
  4. a paragraph that is one bold run is a run-in heading          → <p class="v7-runin">
  5. heading markers "A." / "a." / "1." become a badge              → <span class="v7-mk">
"""
import re

VOID = {'br', 'img', 'input', 'hr', 'meta', 'link', 'source', 'wbr', 'col', 'area', 'base', 'embed', 'track', 'param'}
BLOCK = {'p', 'li', 'td'}
NO_EMPH = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', 'a', 'button', 'svg', 'script', 'style', 'th',
           'code', 'label', 'select', 'option', 'textarea', 'summary'}
SKIP_CLASS = re.compile(r'jsw-interactive-card|zigzag|\brf-|\bch-|orgchart|\bnode\b|annex-file|v7-apps|jx-head|signoff')

TAG = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*?)(/?)>|<!--.*?-->', re.S)

UNIT = r'(?:working\s+|calendar\s+|business\s+)?(?:days?|months?|weeks?|years?|hours?|hrs|minutes?|mins)'
NUM = r'\d+(?:[.,]\d+)*'
KEY = re.compile('|'.join([
    rf'(?:INR|Rs\.?|₹)\s?{NUM}(?:\s?(?:lakhs?|lacs?|crores?|L|K)\b)?(?:\s?(?:-|–|to)\s?{NUM})?',
    rf'(?:[≥≤<>]\s?)?{NUM}(?:\s?(?:-|–|to)\s?{NUM})?\s?%',
    rf'\b{NUM}(?:\s?(?:-|–|to)\s?{NUM})?\s(?:{UNIT})\b',
    r'\b\d{1,2}(?:st|nd|rd|th)\b',
]))
REF = re.compile(r'(?:(?<=nnexure )|(?<=nnexures )|(?<=nnexture )|(?<=NNEXURE )|(?<=form ))\d{1,2}[A-Z]\b')
REF_EM = re.compile(r'^\s*\d{1,2}[A-Z]\b(?!\.)')
LEAD = re.compile(r'^(\s*(?:\(?[0-9ivxIVXa-zA-Z]{1,3}[.)]\s+)?)([A-Z*“"][^–—:;.!?\n]{0,60}?)(\s+[–—-]\s+|:\s+)(?=\S)')
SENTENCE = re.compile(r'^[“"]?(?:The|We|Every|Any|Our|This|It|A|An|Right)\b')
MARK = re.compile(r'^((?:[A-Z]|[a-z]|\d{1,2}|[ivx]{1,4})\.)\s+')


COUNT = {}


def _words(s):
    return len(re.findall(r"[\w’'&/()]+", s))


def _key(text, allow_ref=True):
    """Wrap key facts / form refs in a text segment (already HTML-escaped)."""
    spans = []
    for m in KEY.finditer(text):
        spans.append((m.start(), m.end(), 'v7-key'))
    if allow_ref:
        for m in REF.finditer(text):
            spans.append((m.start(), m.end(), 'v7-ref'))
    spans.sort()
    out, pos = [], 0
    for a, b, cls in spans:
        if a < pos:
            continue
        # don't split an HTML entity
        if '&' in text[max(0, a - 8):a] and ';' not in text[text.rfind('&', 0, a):a]:
            continue
        out.append(text[pos:a] + f'<span class="{cls}">' + text[a:b] + '</span>')
        COUNT[cls] = COUNT.get(cls, 0) + 1
        pos = b
    out.append(text[pos:])
    return ''.join(out)


def emphasize(html):
    stack = []           # (name, skip_flag)
    out, pos = [], 0
    stats = {'lead': 0, 'key': 0, 'ref': 0, 'runin': 0, 'mk': 0}
    block_fresh = False  # next text is the first text of a p/li/td
    leads = []

    def ctx():
        names = [n for n, _ in stack]
        skip = any(s for _, s in stack) or any(n in NO_EMPH for n in names)
        inblock = any(n in BLOCK for n in names)
        return skip, inblock, names

    for m in TAG.finditer(html):
        text = html[pos:m.start()]
        if text:
            skip, inblock, names = ctx()
            if inblock and not skip and text.strip():
                in_em = names and names[-1] == 'em'
                if in_em:
                    if REF_EM.match(text):
                        mm = REF_EM.match(text)
                        text = text[:mm.start()] + text[mm.start():mm.end()].replace(mm.group(0).strip(), f'<span class="v7-ref">{mm.group(0).strip()}</span>', 1) + text[mm.end():]
                        stats['ref'] += 1
                    text = _key(text, allow_ref=False)
                else:
                    lead = ''
                    if block_fresh:
                        lm = LEAD.match(text)
                        rest = text[lm.end():] if lm else ''
                        if (lm and 1 <= _words(lm.group(2)) <= 7 and len(rest) > 2
                                and not SENTENCE.match(lm.group(2))      # "The market … - it's …" is a sentence, not a label
                                and not re.match(r'Sales\b', rest)):    # "Business Head – Sales" is one role name
                            lead = lm.group(1) + f'<strong class="v7-lead">{lm.group(2)}</strong>' + lm.group(3)
                            leads.append(lm.group(2))
                            text = text[lm.end():]
                            stats['lead'] += 1
                    text = lead + _key(text)
            if text.strip():
                block_fresh = False
        out.append(text)
        tag = m.group(0)
        pos = m.end()
        if tag.startswith('<!--'):
            out.append(tag); continue
        close, name, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if close:
            if any(n == name for n, _ in stack):
                while stack:
                    n, _ = stack.pop()
                    if n == name:
                        break
            out.append(tag); continue
        if name in VOID or selfclose:
            out.append(tag); continue
        cm = re.search(r'class="([^"]*)"', attrs)
        skip = bool(cm and SKIP_CLASS.search(cm.group(1)))
        stack.append((name, skip))
        if name in BLOCK:
            block_fresh = True
        out.append(tag)
    out.append(html[pos:])
    res = ''.join(out)

    # 4. run-in headings: <p><strong>…</strong></p> (only that, nothing else)
    def runin(m):
        stats['runin'] += 1
        return '<p class="v7-runin">' + m.group(1) + '</p>'
    res = re.sub(r'<p>(<strong>[^<]*(?:<(?!/?p\b)[^>]*>[^<]*)*</strong>)</p>', runin, res)

    # 5. heading markers → badge (the "." stays in the DOM, visually folded into the badge)
    def mk(m):
        open_, body = m.group(1), m.group(2)
        mm = MARK.match(body)
        if not mm:
            return m.group(0)
        stats['mk'] += 1
        sym = mm.group(1)[:-1]
        cls = 'v7-mk v7-mk-lower' if sym.islower() and len(sym) == 1 else 'v7-mk'
        return open_ + f'<span class="{cls}">{sym}<span class="v7-mk-dot">.</span></span> ' + body[mm.end():]
    res = re.sub(r'(<h[456] class="item-title[^"]*">)([^<]*)', mk, res)
    stats.update({'keys': COUNT.get('v7-key', 0), 'refs': COUNT.get('v7-ref', 0) + stats.pop('ref')}); stats.pop('key')
    return res, stats, leads
