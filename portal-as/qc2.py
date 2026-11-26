#!/usr/bin/env python3
"""QC pass on service.html: contrast, frozen table header/first column, numbered
timeline dots, career-route alignment, click-through infographics.
CSS + JS overlay only (no manual wording changes). Rerunnable."""
import re, sys
from pathlib import Path

CSS = r"""
/* 1. hidden words: emphasis spans on dark chips / panels */
#jxView .as-st-d .v7-key, #jxView .as-smart-card .as-smart-item .v7-key,
#jxView .as-attr li:last-child .v7-key {
  color:#fff !important; background:none !important; box-shadow:none !important; }
#jxView .as-ind-root p { color:#e4e4e7 !important; }
#jxView .as-email-card .as-hdr-lbl { color:#55555c !important; }
#jxView .as-tg td.as-tg-4 { background:#6a6a72 !important; color:#fff !important; }
#jxView .as-tg td.as-tg-4 .v7-lead { color:#fff !important; background:none !important; box-shadow:none !important; }
/* engagement calendar: filtered-out and other-month entries stay readable */
#jxView .calendar-hub .ch-pill.dim { opacity:.68 !important; }
#jxView .calendar-hub .ch-day-cell.outside .ch-day-num { color:#6a6a70 !important; opacity:1 !important; }
/* hover/tap must not bleach dark cells */
#jxView .table-wrap.as-tg table tbody tr:hover td.as-tg-0 { background:#f1f1f2 !important; }
#jxView .table-wrap.as-tg table tbody tr:hover td.as-tg-1 { background:#e1e1e4 !important; }
#jxView .table-wrap.as-tg table tbody tr:hover td.as-tg-2 { background:#c9c9ce !important; }
#jxView .table-wrap.as-tg table tbody tr:hover td.as-tg-3 { background:#a9a9b0 !important; }
#jxView .table-wrap.as-tg table tbody tr:hover td.as-tg-4 { background:#6a6a72 !important; }

/* 2. frozen header row + first column */
#jxView .table-wrap.qc-fit { overflow:clip !important; }
#jxView .table-wrap.qc-fit thead th { position:sticky !important; top:var(--qc-top,60px); z-index:4; background:#151515; }
#jxView .table-wrap.qc-x { overflow-x:auto !important; overscroll-behavior-x:contain; }
#jxView .table-wrap.qc-x thead th { position:relative; z-index:4; background:#151515;
  transform:translateY(var(--qc-y,0px)); }
#jxView .table-wrap.qc-x table { border-collapse:separate; border-spacing:0; }
#jxView .table-wrap.qc-x tbody .qc-c0 { position:sticky !important; left:0; z-index:2; background:#fff !important;
  box-shadow:1px 0 0 rgba(0,0,0,.14), 6px 0 10px -8px rgba(0,0,0,.35) !important; }
#jxView .table-wrap.qc-x tbody tr:nth-child(odd) .qc-c0 { background:#efefed !important; }
#jxView .table-wrap.qc-x thead th.qc-c0 { position:sticky !important; left:0; z-index:6; }
#jxView .table-wrap.qc-x tbody tr th.as-tg-r.qc-c0.qc-c0.qc-c0,
#jxView .table-wrap.qc-x tbody tr td.as-tg-r.qc-c0.qc-c0.qc-c0 { background:#151515 !important; color:#fff !important; }
@media (max-width:760px){
  #jxView .table-wrap.qc-x .qc-c0 { width:116px; min-width:104px !important; max-width:132px; overflow-wrap:break-word; }
  #jxView .table-wrap.qc-x table :is(th,td).qc-c0 { white-space:normal !important; overflow-wrap:anywhere; }
  #jxView .table-wrap.qc-x table thead th.qc-c0 { font-size:10px !important; letter-spacing:.02em !important;
    padding-left:8px !important; padding-right:6px !important; }
}

/* 3. timeline markers carry the step number */
#jxView .as-steps { counter-reset:qcs; }
#jxView .as-steps .as-st-n.is-dot { counter-increment:qcs; display:flex !important; align-items:center; justify-content:center;
  background:#151515 !important; }
#jxView .as-steps .as-st-n.is-dot::before { content:none !important; }
#jxView .as-steps .as-st-n.is-dot::after { content:counter(qcs) !important; position:static !important; display:block !important;
  width:auto !important; height:auto !important; inset:auto !important; background:none !important; border:0 !important;
  box-shadow:none !important; transform:none !important; color:#fff; font-size:15px; font-weight:800; line-height:1; }

/* 4. career-route card alignment */
#jxView .img-card:has(.as-ladder) .as-legend { margin:0 !important; padding:18px 18px 2px; }
#jxView .img-card:has(.as-ladder) .as-ladder { margin:0 !important; padding:14px 18px 18px; }
#jxView .img-card:has(.as-ladder) .img-caption { padding-left:18px; padding-right:18px; }
@media (max-width:760px){
  #jxView .img-card:has(.as-ladder) .as-legend { display:none; }
  #jxView .img-card:has(.as-ladder) .as-ladder { padding:12px; }
}

/* 5. click-through infographics */
/* indicator is its own element: ::before/::after belong to the flow connectors */
#jxView .qc-go { cursor:pointer; }
#jxView li.qc-go { position:relative; padding-right:26px; }
#jxView .qc-ic { position:absolute; top:9px; right:9px; width:13px; height:13px; margin:0; opacity:.55; pointer-events:none;
  background:currentColor; -webkit-mask:var(--qc-arrow) center/contain no-repeat; mask:var(--qc-arrow) center/contain no-repeat;
  --qc-arrow:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='M4 12 12 4M5 4h7v7' fill='none' stroke='black' stroke-width='2.4'/%3E%3C/svg%3E"); }
#jxView li.qc-go > .qc-ic { top:50%; right:5px; transform:translateY(-50%); }
#jxView .qc-go:hover > .qc-ic { opacity:1; }
#jxView .qc-go:hover { outline:2px solid #151515; outline-offset:2px; border-radius:12px; }
#jxView .qc-go:focus-visible { outline:3px solid #151515; outline-offset:3px; }
#jxView .qc-flash { animation:qcflash 2.2s ease-out; border-radius:8px; }
@keyframes qcflash { 0%,45% { box-shadow:0 0 0 4px rgba(168,129,43,.85); background-color:rgba(168,129,43,.16); }
  100% { box-shadow:0 0 0 4px rgba(168,129,43,0); background-color:transparent; } }
"""

JS = r"""
(function(){
  var view = document.getElementById('jxView'); if(!view) return;
  var $$ = function(s,r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)); };
  var norm = function(s){ return (s||'').replace(/\s+/g,' ').trim(); };

  /* ---------- sticky offset ---------- */
  function topEdge(){
    var edge = 0;
    $$('.jx-top, .jx-chips').forEach(function(el){
      var s = getComputedStyle(el); if(s.position!=='fixed' && s.position!=='sticky') return;
      var r = el.getBoundingClientRect(); if(!r.height) return;
      var stick = parseFloat(s.top)||0;
      if(r.top <= stick+1 && r.bottom > edge) edge = r.bottom;
    });
    return Math.max(0, Math.round(edge));
  }

  /* ---------- tables ---------- */
  function markFirstColumn(t){
    var filled = [];
    $$('tr', t).filter(function(tr){ return tr.closest('table')===t; }).forEach(function(tr,y){
      var x = 0; filled[y] = filled[y]||[];
      Array.prototype.forEach.call(tr.cells, function(c){
        while(filled[y][x]) x++;
        c.classList.toggle('qc-c0', x===0 && c.colSpan===1);
        for(var i=0;i<c.rowSpan;i++){ filled[y+i]=filled[y+i]||[]; for(var j=0;j<c.colSpan;j++) filled[y+i][x+j]=1; }
        x += c.colSpan;
      });
    });
  }
  function sizeTables(){
    $$('.table-wrap', view).forEach(function(w){
      var t = w.querySelector('table'); if(!t || !w.clientWidth) return;
      markFirstColumn(t);
      var wide = t.offsetWidth > w.clientWidth + 2;
      w.classList.toggle('qc-x', wide); w.classList.toggle('qc-fit', !wide);
      if(!wide) w.style.removeProperty('--qc-y');
    });
    place();
  }
  function place(){
    var edge = topEdge();
    document.documentElement.style.setProperty('--qc-top', edge+'px');
    $$('.table-wrap.qc-x', view).forEach(function(w){
      var t = w.querySelector('table'), h = t && t.tHead; if(!h) return;
      var r = t.getBoundingClientRect(); if(!r.height) return;
      var last = t.rows[t.rows.length-1].offsetHeight;
      var max = Math.max(0, r.height - h.offsetHeight - last);
      var y = Math.min(max, Math.max(0, edge - r.top));
      w.style.setProperty('--qc-y', Math.round(y)+'px');
    });
  }
  var ticking = false;
  addEventListener('scroll', function(){ if(ticking) return; ticking = true;
    requestAnimationFrame(function(){ ticking = false; place(); }); }, {passive:true, capture:true});

  /* ---------- click-through infographics ---------- */
  function h(route, start){ return {route:route, sel:'h4,h5,p.v7-runin', start:start}; }
  var FLOWS = {
    'ch3-1': ['3.1.1','3.1.2','3.1.3','3.1.4','3.1.5','3.1.6','3.1.7','3.1.8','3.1.9','3.1.11','3.1.12'].map(function(n){ return h('ch3-1', n+' '); }),
    'ch5-1': ['5.1.1','5.1.2','5.1.3','5.1.4','5.1.5','5.1.6','5.1.7','5.1.8','5.1.8'].map(function(n){ return h('ch5-1', n+' '); }),
    'ch5-2': ['5.2.1','5.2.2','5.2.3'].map(function(n){ return h('ch5-2', n+' '); }),
    'ch7-2': ['7.2.1','7.2.1','7.2.1','7.2.1','7.2.2','7.2.2','7.2.3','7.2.3','7.2.3','7.2.3'].map(function(n){ return h('ch7-2', n+' '); }),
    'ch8-2': [h('ch3-1','How to make an IJP'), null, h('ch8-2','Eligibility for Promotion'), h('ch3-1','3.1.6 '),
              null, {annex:'annex-8A'}, null, null],
    'ch11-1': [1,2,3,4,5,6,7,8,9].map(function(n){ return h('ch11-1','11.1.'+n+' '); })
  };
  FLOWS['ch8-2'][0].sel = 'h4,h5,p,.as-ijp-title';
  var CYCLE = ['7.2.1','7.2.2','7.2.2','7.2.3','7.2.3'];
  var LEVELS = [[/^Manpower planning/,'ch3'],[/^Compensation/,'ch4'],[/^Performance management/i,'ch7'],
    [/^Training/,'ch6'],[/^Career planning/,'ch8'],[/^Employee engagement/,'ch9'],[/^Succession/,'ch13-1'],
    [/^Communication/,'ch13-2'],[/^Leadership/,'ch13-3']];

  /* section id that precedes an element in document order */
  function sectionOf(el){
    var id = '';
    $$('h3.sub-title[id]', view).forEach(function(s){
      if(s.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING) id = s.id; });
    return id;
  }
  function arm(el, target){
    if(!el || !target || el.classList.contains('qc-go')) return;
    el.classList.add('qc-go'); el.setAttribute('role','button'); el.tabIndex = 0; el._qc = target;
    if(getComputedStyle(el).position==='static') el.style.position = 'relative';
    var ic = document.createElement('i'); ic.className = 'qc-ic'; ic.setAttribute('aria-hidden','true'); el.appendChild(ic);
  }
  function wire(){
    $$('.fx-flow', view).forEach(function(f){
      if(f.closest('figure')) return;
      var map = FLOWS[sectionOf(f)], nodes = $$('.fx-node', f);
      if(map && map.length===nodes.length) nodes.forEach(function(n,i){ arm(n, map[i]); });
    });
    $$('figure', view).forEach(function(fig){
      var sec = sectionOf(fig);
      var steps = $$('.fx-chev-step', fig);
      if(sec==='ch7-1' && steps.length===CYCLE.length)
        steps.forEach(function(n,i){ arm(n, h('ch7-2', CYCLE[i]+' ')); });
      $$('.fx-node.fx-letter, .fx-node:has(> .fx-big)', fig).forEach(function(n){
        var name = n.querySelector('.fx-vhead'); if(sec==='ch7-2' && name)
          arm(n, {route:'ch7-2', sel:'.as-smart-name', start:norm(name.textContent), up:'.as-smart-item'});
      });
    });
    $$('.as-level-l li', view).forEach(function(li){
      var t = norm(li.textContent);
      LEVELS.forEach(function(m){ if(m[0].test(t)) arm(li, {route:m[1], top:true}); });
    });
  }

  function find(tg){
    var hit = $$(tg.sel, view).filter(function(e){
      return norm(e.textContent).indexOf(tg.start)===0 && e.getClientRects().length; })[0];
    return hit && tg.up ? hit.closest(tg.up) : hit;
  }
  function reveal(el){
    $$('.reveal', view).forEach(function(r){ if(r.contains(el)||el.contains(r)) r.classList.add('in','visible','is-in'); });
    var go = function(smooth){
      var off = (document.querySelector('.jx-top')||{}).offsetHeight || 60;
      var chips = document.querySelector('.jx-chips'); if(chips) off += chips.offsetHeight;
      scrollTo({top: Math.max(0, el.getBoundingClientRect().top + scrollY - off - 20), behavior: smooth?'smooth':'instant'});
    };
    go(true);
    setTimeout(function(){ var t = el.getBoundingClientRect().top; if(t<40 || t>innerHeight*0.6) go(false); }, 900);
    el.classList.remove('qc-flash'); void el.offsetWidth; el.classList.add('qc-flash');
    setTimeout(function(){ el.classList.remove('qc-flash'); }, 2400);
  }
  function jump(tg){
    if(tg.annex){ var a = view.querySelector('.fx-flow a[href="#'+tg.annex+'"]'); if(a) a.click(); return; }
    if(tg.top){ location.hash = tg.route; return; }
    var el = find(tg); if(el) return reveal(el);
    location.hash = tg.route;
    var n = 0, iv = setInterval(function(){ var e = find(tg); if(e || ++n>25){ clearInterval(iv); if(e) setTimeout(function(){ reveal(e); }, 350); } }, 100);
  }
  view.addEventListener('click', function(e){
    var el = e.target.closest('.qc-go'); if(!el || e.target.closest('a')) return;
    jump(el._qc);
  });
  view.addEventListener('keydown', function(e){
    if(e.key!=='Enter' && e.key!==' ') return;
    var el = e.target.closest('.qc-go'); if(!el || e.target.closest('a')) return;
    e.preventDefault(); jump(el._qc);
  });

  var timer;
  function refresh(){ clearTimeout(timer); timer = setTimeout(function(){ wire(); sizeTables(); }, 80); }
  new MutationObserver(refresh).observe(view, {childList:true, subtree:true, attributes:true, attributeFilter:['class','hidden']});
  addEventListener('resize', refresh); addEventListener('hashchange', refresh); addEventListener('load', refresh);
  if(document.fonts) document.fonts.ready.then(refresh);
  refresh();
})();
"""

BLOCK = re.compile(r'\n?<!--qc2-->.*?<!--/qc2-->\n?', re.S)


def apply(h):
    h = BLOCK.sub('', h)
    i = h.rindex('</body>')
    add = f'<!--qc2--><style id="as-qc2">{CSS}</style><script id="as-qc2-js">{JS}</script><!--/qc2-->\n'
    out = h[:i] + add + h[i:]
    assert BLOCK.sub('', out).replace('\n', '') == h.replace('\n', ''), 'content changed'
    return out


if __name__ == '__main__':
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'service.html'
    p.write_text(apply(p.read_text()))
    print('qc2 applied to', p)
