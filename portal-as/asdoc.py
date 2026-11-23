"""Service (After-Sales) HR manual: docx model on top of portal-v7/build.py's Doc.

* the four chapter files are read as one block stream
* DrawingML shape groups (learner journey, TNA, calendar, cycle ...) are parsed into 'shape' blocks
* numbered headings ("3.1.1 …") that are Normal paragraphs become headings
"""
import os, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'portal-v7'))
os.environ.setdefault('JX_DOCX', str(Path.home() / 'Downloads' / 'HR Manual V9 13.10.26.docx'))
import build as B                      # noqa: E402  (Doc, Renderer, table helpers)
from docx.oxml.ns import qn            # noqa: E402
from docx.text.paragraph import Paragraph  # noqa: E402

SRC_DIR = Path.home() / 'Downloads' / 'HR_OS_Chapters'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
      'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}


def accepted(i, tmp):
    src = next(SRC_DIR.glob(f'{i}. *.docx'))
    dst = Path(tmp) / f'acc{i}.docx'
    subprocess.run([sys.executable, str(HERE / 'accept2.py'), str(src), str(dst)], check=True)
    return dst


def parse_shapes(el):
    """Shapes of every drawing group in paragraph `el` (mc:Choice only), in document order, each as a dict."""
    out = []
    for ac in el.iter('{%s}AlternateContent' % NS['mc']):
        ch = ac.find('mc:Choice', NS)
        grp = []
        for sp in ch.iter('{%s}wsp' % NS['wps']):
            paras = []
            for p in sp.findall('.//w:txbxContent//w:p', NS):
                # a run break (w:br) inside a paragraph is a line break
                t = ''
                for n in p.iter():
                    if n.tag == qn('w:t'): t += n.text or ''
                    elif n.tag == qn('w:br'): t += '\n'
                    elif n.tag == qn('w:tab'): t += ' '
                t = t.strip()
                if t:
                    paras.append(t)
            off, ext = sp.find('.//a:off', NS), sp.find('.//a:ext', NS)
            geom = sp.find('.//a:prstGeom', NS)
            fill = sp.find('.//wps:spPr/a:solidFill/a:srgbClr', NS)
            grp.append({'x': int(off.get('x')) / 12700, 'y': int(off.get('y')) / 12700,
                        'w': int(ext.get('cx')) / 12700, 'h': int(ext.get('cy')) / 12700,
                        'prst': geom.get('prst') if geom is not None else '',
                        'fill': fill.get('val') if fill is not None else '', 'paras': paras})
        out.append(grp)
    return out


H3_RE = re.compile(r'^\d{1,2}\.\d{1,2}\.\d{1,2}\s+\S')     # 13.1.1 Critical roles
H2_RE = re.compile(r'^\d{1,2}\.\d{1,2}\s+\S')              # 13.1 Succession Planning


class ASDoc(B.Doc):
    plain_headings = False      # chapter 13: no heading colours in the file, numbers carry the structure

    def block(self, el):
        shapes = None
        if el.tag == qn('w:p') and el.find('.//{%s}AlternateContent' % NS['mc']) is not None:
            shapes = parse_shapes(el)
        b = super().block(el)
        if b is not None and b['k'] == 'p' and not b['lvl'] and not b['num']:
            t = b['text']
            if self.plain_headings and len(t) < 90 and not t.endswith('.'):
                if H3_RE.match(t): b['lvl'] = 3
                elif H2_RE.match(t): b['lvl'] = 2
        if b is not None and b['k'] == 'p' and b['num'] is not None and not b['lvl']:
            # numbered heading paragraph ("3.1.7 Interview round 1 and round 2" is auto-numbered, 14pt blue)
            sizes, colors, _ = self.fmt(b['p'])
            if B.HEAD_BLUE in colors and max([s for s in sizes if s] or [0]) >= 13.5:
                b['lvl'] = 3
        if shapes:
            sb = {'k': 'shape', 'groups': shapes, 'text': ''}
            if b is None:
                return sb
            b['shapes'] = sb
        return b

    def __init__(self, path, **kw):
        self.plain_headings = kw.pop('plain_headings', False)
        super().__init__(path)
        flat = []
        for b in self.blocks:
            if b.get('shapes'):
                flat.append(b['shapes'])
            flat.append(b)
        self.blocks = flat


def load_all(tmp):
    docs = []
    for i in (1, 2, 3, 4):
        docs.append(ASDoc(accepted(i, tmp), plain_headings=(i == 4)))
    return docs
