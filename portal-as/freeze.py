#!/usr/bin/env python3
"""Frozen table header + first column for v2.html: the table part of qc2.py only,
with v2's own colours. CSS + JS overlay, no wording changes. Rerunnable.
Usage: python3 portal-as/freeze.py [file ...]   (default: v2.html hr-manual-2.html)"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qc2


def cut(s, a, b):
    return s[s.index(a):s.index(b)]


CSS = cut(qc2.CSS, '/* 2. frozen', '/* 3. timeline')
CSS = CSS.replace('.as-tg-r', '.qc-none').replace('#151515', '#111113')
CSS += r"""
#jxView .table-wrap.qc-x tbody tr:nth-child(odd) .qc-c0 { background:#fff !important; }
#jxView .table-wrap.qc-x tbody tr:nth-child(even) .qc-c0 { background:#fafaf9 !important; }
#jxView .table-wrap.qc-x table.v7-day-table tbody tr .qc-c0 { background:#f4f4f2 !important; }
"""

JS = ('(function(){\n'
      "  var view = document.getElementById('jxView'); if(!view) return;\n"
      '  var $$ = function(s,r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)); };\n  '
      + cut(qc2.JS, '/* ---------- sticky offset', '/* ---------- click-through')
      + """var timer;
  function refresh(){ clearTimeout(timer); timer = setTimeout(sizeTables, 80); }
  new MutationObserver(refresh).observe(view, {childList:true, subtree:true, attributes:true, attributeFilter:['class','hidden']});
  addEventListener('resize', refresh); addEventListener('hashchange', refresh); addEventListener('load', refresh);
  if(document.fonts) document.fonts.ready.then(refresh);
  refresh();
})();
""")

BLOCK = re.compile(r'\n?<!--frz-->.*?<!--/frz-->\n?', re.S)


def apply(h):
    h = BLOCK.sub('', h)
    i = h.rindex('</body>')
    add = f'<!--frz--><style id="jx-frz">{CSS}</style><script id="jx-frz-js">{JS}</script><!--/frz-->\n'
    out = h[:i] + add + h[i:]
    assert BLOCK.sub('', out).replace('\n', '') == h.replace('\n', ''), 'content changed'
    return out


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    for p in [Path(a) for a in sys.argv[1:]] or [root / 'v2.html', root / 'hr-manual-2.html']:
        p.write_text(apply(p.read_text()))
        print('freeze applied to', p.name)
