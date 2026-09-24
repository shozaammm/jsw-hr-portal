/* ==========================================================================
   JSW HR Operations Manual — app shell behaviour
   --------------------------------------------------------------------------
   Data comes from two places only:
     • JX_TOC           — the manual's table of contents (copied verbatim)
     • the chapter DOM  — the manual's own sections, rendered verbatim
   Every label shown by the shell is read from one of those. No manual text
   is generated or rewritten; sub-section "pages" are the chapter's own
   blocks shown one range at a time.

   Contents
     1 helpers            5 home (filters + cards)
     2 model              6 search palette
     3 navigation list    7 phone sheet, tab bar, progress
     4 router + render    8 compat globals + boot
   ========================================================================== */
(function(){
  'use strict';

  var doc = document, root = doc.documentElement;
  var TOC = window.JX_TOC || [];
  var REDUCED = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var wide = window.matchMedia ? matchMedia('(min-width:1024px)') : { matches: true };
  var MODE_KEY = 'jxReadMode';               // 'pages' | 'full'

  /* ------------------------------------------------------------ 1 helpers */
  function $(sel, ctx){ return (ctx || doc).querySelector(sel); }
  function $$(sel, ctx){ return [].slice.call((ctx || doc).querySelectorAll(sel)); }
  function esc(s){ var d = doc.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
  function el(tag, cls, html){ var n = doc.createElement(tag); if(cls) n.className = cls; if(html != null) n.innerHTML = html; return n; }
  function store(v){
    try{ if(v === undefined) return localStorage.getItem(MODE_KEY); localStorage.setItem(MODE_KEY, v); }catch(e){}
    return null;
  }
  function cssPx(name){ var v = parseFloat(getComputedStyle(root).getPropertyValue(name)); return isNaN(v) ? 0 : v; }
  function headOffset(){ return cssPx('--jx-top-h') + (wide.matches ? 0 : ($('.jx-chapter:not([hidden]) .jx-chips') ? 52 : 0)) + 16; }
  function docTop(n){ return n.getBoundingClientRect().top + window.pageYOffset; }
  function jumpY(y){ window.scrollTo(0, Math.max(0, y)); }
  function smoothY(y){ window.scrollTo({ top: Math.max(0, y), behavior: REDUCED ? 'auto' : 'smooth' }); }
  function replay(n, cls){ if(!n || REDUCED) return; n.classList.remove(cls); void n.offsetWidth; n.classList.add(cls); }
  function numLabel(num, label){ return (num ? '<b>' + esc(num) + '</b>' : '') + '<span>' + esc(label) + '</span>'; }
  var ICON_NEXT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
  var ICON_PREV = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>';
  var ICON_FULL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
  var ICON_PAGES = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="4" width="14" height="16" rx="2"/><path d="M9 9h6M9 13h6"/></svg>';

  /* -------------------------------------------------------------- 2 model */
  // One chapter per TOC item; one page per sub-section when the chapter's
  // sub-section headings are sibling blocks of its prose.
  var chapters = [], pageIndex = {}, groups = [];

  TOC.forEach(function(g, gi){
    var parts = String(g.group).split(' · ');
    var group = { idx: gi, full: g.group, short: parts[0], name: parts.slice(1).join(' · '), chapters: [] };
    groups.push(group);
    (g.items || []).forEach(function(it){
      var article = doc.getElementById('chap-' + it.id);
      var section = doc.getElementById(it.id);
      if(!article || !section) return;
      var prose = section.querySelector(':scope > .prose');
      var ch = {
        id: it.id, num: it.num, label: it.label, group: group,
        article: article, section: section, prose: prose,
        head: $('.jx-head', article),
        title: ($('.jx-h1', article) || {}).textContent || it.label,
        subs: it.subs || [], pages: [], pageable: false, full: false, page: 0
      };
      buildPages(ch);
      ch.idx = chapters.length;
      chapters.push(ch);
      group.chapters.push(ch);
    });
  });

  function buildPages(ch){
    var kids = ch.prose ? [].slice.call(ch.prose.children) : [];
    var anchors = ch.subs.map(function(s){ return doc.getElementById(s.id); });
    var starts = anchors.map(function(a){ return a && a.parentElement === ch.prose ? kids.indexOf(a) : -1; });
    ch.pageable = ch.subs.length > 1 && starts.every(function(s, i){ return s >= 0 && (i === 0 || s > starts[i - 1]); });

    if(ch.pageable){
      var lead = kids.slice(0, starts[0]).filter(function(n){ return n.tagName !== 'SCRIPT'; });
      if(lead.length) ch.pages.push({ id: ch.id, num: '', label: ch.title, nodes: kids.slice(0, starts[0]), lead: true });
      ch.subs.forEach(function(s, i){
        var end = i + 1 < starts.length ? starts[i + 1] : kids.length;
        ch.pages.push({ id: s.id, num: s.num, label: s.label, nodes: kids.slice(starts[i], end) });
      });
      if(!lead.length) ch.pages[0].alias = ch.id;
    } else {
      ch.pages.push({ id: ch.id, num: '', label: ch.title, nodes: null, lead: true });
    }
    ch.pages.forEach(function(p, i){
      p.idx = i; p.ch = ch;
      pageIndex[p.id] = p;
      if(p.alias) pageIndex[p.alias] = p;
    });
    // chapters that cannot be paged still expose their sub-sections as jumps
    ch.jumps = ch.pageable ? [] : ch.subs.map(function(s){ return { id: s.id, num: s.num, label: s.label }; });
  }

  function allPages(){
    var out = [];
    chapters.forEach(function(ch){ ch.pages.forEach(function(p){ out.push(p); }); });
    return out;
  }
  var flatPages = allPages();

  // Where does an id live? A page id, or any element inside a chapter.
  function locate(id){
    if(!id || id === 'home') return null;
    if(pageIndex[id]) return { page: pageIndex[id], target: null };
    var t = doc.getElementById(id);
    if(!t) return null;
    var art = t.closest ? t.closest('.jx-chapter') : null;
    if(!art) return null;
    var ch = chapters.filter(function(c){ return c.article === art; })[0];
    if(!ch) return null;
    return { page: pageOf(ch, t), target: t };
  }
  function pageOf(ch, node){
    if(!ch.pageable) return ch.pages[0];
    for(var i = 0; i < ch.pages.length; i++){
      var ns = ch.pages[i].nodes;
      for(var j = 0; j < ns.length; j++){ if(ns[j] === node || ns[j].contains(node)) return ch.pages[i]; }
    }
    return ch.pages[0];
  }

  /* --------------------------------------------------- 3 navigation list */
  var navList = $('#jxNavList');
  var navRefs = {};                      // chapter id -> { wrap, item, subs:{id:btn} }

  (function buildNav(){
    var home = el('button', 'jx-nav-item jx-nav-home', '<span class="jx-nav-num"></span><span>Home</span>');
    home.type = 'button';
    home.setAttribute('data-go', 'home');
    navList.appendChild(home);

    groups.forEach(function(g){
      if(!g.chapters.length) return;
      var box = el('div', 'jx-nav-group');
      box.appendChild(el('div', 'jx-nav-group-label',
        g.name ? '<b>' + esc(g.short) + '</b><span>' + esc(g.name) + '</span>' : '<b>' + esc(g.short) + '</b>'));
      g.chapters.forEach(function(ch){
        var wrap = el('div', 'jx-nav-chapter');
        var item = el('button', 'jx-nav-item', '<span class="jx-nav-num">' + esc(ch.num) + '</span><span>' + esc(ch.label) + '</span>');
        item.type = 'button';
        item.addEventListener('click', function(){ go(ch.pages[0].alias || ch.pages[0].id); });
        wrap.appendChild(item);
        var refs = { wrap: wrap, item: item, subs: {} };
        var list = ch.pageable ? ch.pages.filter(function(p){ return !p.lead; }) : ch.jumps;
        if(list.length){
          var subs = el('div', 'jx-nav-subs'), inner = el('div');
          list.forEach(function(p){
            var b = el('button', 'jx-nav-sub', '<b>' + esc(p.num) + '</b><span>' + esc(p.label) + '</span>');
            b.type = 'button';
            b.addEventListener('click', function(){ go(p.id); });
            inner.appendChild(b);
            refs.subs[p.id] = b;
          });
          subs.appendChild(inner);
          wrap.appendChild(subs);
        }
        navRefs[ch.id] = refs;
        box.appendChild(wrap);
      });
      navList.appendChild(box);
    });
  })();

  function paintNav(page, spyId){
    Object.keys(navRefs).forEach(function(id){
      var r = navRefs[id], on = !!page && page.ch.id === id;
      r.wrap.classList.toggle('is-open', on);
      r.item.classList.toggle('is-active', on);
      r.item.classList.toggle('is-page', on && (!!page.lead && !page.ch.full));
      Object.keys(r.subs).forEach(function(sid){
        var cur = on && (page.ch.full || !page.ch.pageable ? sid === spyId : sid === page.id);
        r.subs[sid].classList.toggle('is-page', cur);
      });
    });
    var homeBtn = $('.jx-nav-home');
    if(homeBtn) homeBtn.classList.toggle('is-page', !page);
    // keep the current entry visible in the sidebar (after the sub-list opens)
    if(wide.matches && page && !spyId){
      var act = $('.jx-nav-sub.is-page', navList) || (navRefs[page.ch.id] || {}).item;
      if(act) setTimeout(function(){
        var box = navList.getBoundingClientRect(), r = act.getBoundingClientRect();
        if(r.top < box.top + 8 || r.bottom > box.bottom - 8){
          navList.scrollTo({ top: navList.scrollTop + r.top - box.top - box.height / 3, behavior: REDUCED ? 'auto' : 'smooth' });
        }
      }, 480);
    }
  }

  /* -------------------------------------------- chapter chrome (per chapter) */
  chapters.forEach(function(ch){
    // chips: phone/tablet sub-section tabs
    var list = ch.pageable ? ch.pages : ch.jumps;
    if(list.length > 1){
      var chips = el('nav', 'jx-chips');
      chips.setAttribute('aria-label', 'Sections');
      ch.chipRefs = {};
      list.forEach(function(p){
        var c = el('button', 'jx-chip', numLabel(p.num, p.lead ? ch.title : p.label));
        c.type = 'button';
        c.title = (p.num ? p.num + ' ' : '') + p.label;
        c.addEventListener('click', function(){ go(p.id); });
        chips.appendChild(c);
        ch.chipRefs[p.id] = c;
      });
      ch.head.parentNode.insertBefore(chips, ch.head.nextSibling);
      ch.chips = chips;
      ch.article.classList.add('jx-has-chips');
    }
    // full chapter / by section toggle
    if(ch.pageable){
      var mode = el('button', 'jx-mode');
      mode.type = 'button';
      mode.addEventListener('click', function(){
        ch.full = !ch.full;
        store(ch.full ? 'full' : 'pages');
        var p = ch.full ? ch.pages[0] : (spyPage(ch) || ch.pages[0]);
        go(p.alias || p.id);
      });
      $('.jx-head-row', ch.article).appendChild(mode);
      ch.modeBtn = mode;
    }
    // pager
    var pager = el('nav', 'jx-pager');
    pager.setAttribute('aria-label', 'Continue reading');
    ch.article.appendChild(pager);
    ch.pager = pager;
  });

  function spyPage(ch){
    var line = headOffset() + 40, found = null;
    ch.pages.forEach(function(p){
      var n = p.nodes && p.nodes[0];
      if(n && n.getBoundingClientRect().top <= line) found = p;
    });
    return found;
  }

  function pagerHtml(kind, p){
    var label = p.lead && p.ch !== current.ch ? p.ch.title : p.label;
    var num = p.lead ? (p.ch !== current.ch ? p.ch.num : '') : p.num;
    var k = kind === 'next' ? 'Next' : 'Previous';
    var body = '<div><span class="jx-pager-k">' + k + '</span><span class="jx-pager-t">' + (num ? '<b>' + esc(num) + '</b>' : '') + esc(label) + '</span></div>';
    return kind === 'next' ? body + ICON_NEXT : ICON_PREV + body;
  }

  // Reading order runs through the whole manual: next page, then next chapter.
  function neighbours(page){
    var ch = page.ch;
    if(ch.full || !ch.pageable){
      var pc = chapters[ch.idx - 1], nc = chapters[ch.idx + 1];
      return { prev: pc ? pc.pages[0] : null, next: nc ? nc.pages[0] : null };
    }
    var i = flatPages.indexOf(page);
    return { prev: flatPages[i - 1] || null, next: flatPages[i + 1] || null };
  }

  /* ---------------------------------------------------- 4 router + render */
  var homeEl = $('#jxHome'), view = $('#jxView'), crumb = $('#jxCrumb');
  var current = { page: null, ch: null };

  function go(id, opts){
    opts = opts || {};
    id = id || 'home';
    var hash = id === 'home' ? '' : id;
    if(('#' + hash) === location.hash || (hash === '' && !location.hash)){
      route(opts);               // same address: render in place
    } else {
      pendingOpts = opts;
      if(hash === '') history.pushState(null, '', location.pathname + location.search);
      else history.pushState(null, '', '#' + hash);
      route(opts);
    }
  }
  var pendingOpts = null;

  function route(opts){
    opts = opts || pendingOpts || {};
    pendingOpts = null;
    var id = decodeURIComponent(location.hash.slice(1));
    var loc = locate(id);
    if(!loc){ showHome(opts); return; }
    show(loc.page, loc.target, opts);
  }

  // Runs `fn` (the DOM swap) inside a view transition when available, then
  // `after` once the new state is in the DOM.
  function transition(fn, animateEl, after, inPlace){
    closeNav();
    after = after || function(){};
    if(inPlace){ fn(); after(); return; }
    if(!REDUCED && doc.startViewTransition){
      root.classList.add('jx-vt');
      var t = doc.startViewTransition(fn);
      var done = function(){ root.classList.remove('jx-vt'); };
      t.ready.catch(function(){});           // a newer navigation may skip this one
      t.finished.then(done, done);
      t.updateCallbackDone.then(after, after);
    } else {
      fn();
      replay(animateEl, 'jx-enter');
      after();
    }
  }

  function showHome(opts){
    transition(function(){
      chapters.forEach(function(c){ c.article.hidden = true; });
      homeEl.hidden = false;
      current = { page: null, ch: null };
      crumb.innerHTML = '';
      paintNav(null);
      paintTabs('home');
      doc.title = 'JSW HR Operations Manual';
      jumpY(0);
      replay(homeEl, 'jx-play');
    }, homeEl, afterRender, opts && opts.inPlace);
  }

  function show(page, target, opts){
    opts = opts || {};
    var ch = page.ch;
    var sameChapter = current.ch === ch;
    var render = function(){
      homeEl.hidden = true;
      chapters.forEach(function(c){ c.article.hidden = c !== ch; });
      if(!sameChapter && ch.pageable) ch.full = store() === 'full' && !(target || opts.query);
      applyPage(ch, page);
      current = { page: page, ch: ch };
      paintHead(ch, page);
      paintCrumb(ch, page);
      paintPager(page);
      paintNav(page, target && target.id);
      paintTabs(null);
      doc.title = (page.lead ? ch.title : (page.num ? page.num + ' ' : '') + page.label) + ' · JSW HR Operations Manual';
      if(target){
        requestAnimationFrame(function(){ jumpY(docTop(target) - headOffset()); });
      } else if(ch.full && !page.lead){
        var first = page.nodes && page.nodes[0];
        requestAnimationFrame(function(){ if(first) jumpY(docTop(first) - headOffset()); });
      } else {
        jumpY(0);
      }
    };
    transition(render, ch.article, function(){
      afterRender();
      if(opts.query) revealQuery(page, opts.query);
    }, opts.inPlace);
  }

  function applyPage(ch, page){
    if(!ch.pageable) return;
    ch.pages.forEach(function(p){
      var off = !ch.full && p !== page;
      p.nodes.forEach(function(n){ n.classList.toggle('jx-off', off); });
    });
    // the first heading of a sub-section page reads as the page title
    ch.pages.forEach(function(p){
      if(p.lead) return;
      var h = p.nodes[0];
      if(h) h.classList.toggle('jx-lead', !ch.full && p === page);
    });
    ch.page = page.idx;
  }

  function paintHead(ch, page){
    var sub = ch.pageable && !ch.full && !page.lead;
    ch.head.classList.toggle('is-sub', sub);
    if(ch.modeBtn){
      ch.modeBtn.innerHTML = ch.full ? ICON_PAGES + '<span>By section</span>' : ICON_FULL + '<span>Full chapter</span>';
      ch.modeBtn.setAttribute('aria-pressed', String(ch.full));
      ch.modeBtn.title = ch.full ? 'By section' : 'Full chapter';
    }
    if(ch.chipRefs){
      Object.keys(ch.chipRefs).forEach(function(id){
        ch.chipRefs[id].classList.toggle('is-page', ch.pageable && !ch.full ? id === page.id : false);
      });
      var on = ch.pageable && !ch.full ? ch.chipRefs[page.id] : null;
      centerChip(ch.chips, on);
    }
  }

  function centerChip(bar, chip){
    if(!bar || !chip) return;
    requestAnimationFrame(function(){
      bar.scrollTo({ left: Math.max(0, chip.offsetLeft - (bar.clientWidth - chip.offsetWidth) / 2), behavior: REDUCED ? 'auto' : 'smooth' });
    });
  }

  function paintCrumb(ch, page){
    var parts = [];
    parts.push('<button type="button" data-go="home">Home</button><span class="jx-crumb-sep">/</span>');
    if(!page.lead && ch.pageable && !ch.full){
      parts.push('<button type="button" data-crumb="' + esc(ch.pages[0].alias || ch.pages[0].id) + '">' + esc(ch.title) + '</button><span class="jx-crumb-sep">/</span>');
      parts.push('<span class="jx-crumb-now">' + esc((page.num ? page.num + ' ' : '') + page.label) + '</span>');
    } else {
      parts.push('<span class="jx-crumb-now">' + esc(ch.title) + '</span>');
    }
    crumb.innerHTML = parts.join('');
  }

  function paintPager(page){
    var ch = page.ch, n = neighbours(page);
    ch.pager.innerHTML = '';
    if(n.prev){
      var p = el('button', 'jx-pager-btn jx-pager-prev', pagerHtml('prev', n.prev));
      p.type = 'button';
      p.addEventListener('click', function(){ go(n.prev.alias || n.prev.id); });
      ch.pager.appendChild(p);
    }
    if(n.next){
      var x = el('button', 'jx-pager-btn jx-pager-next', pagerHtml('next', n.next));
      x.type = 'button';
      x.addEventListener('click', function(){ go(n.next.alias || n.next.id); });
      ch.pager.appendChild(x);
    }
  }

  // Components measure themselves on resize (diagrams, org chart lines).
  function afterRender(){
    requestAnimationFrame(function(){
      try{ window.dispatchEvent(new Event('resize')); }catch(e){}
      if(typeof window.scaleAllDiagrams === 'function') window.scaleAllDiagrams();
      progress();
      requestAnimationFrame(fitWide);
    });
  }

  // A content block wider than the reading column (fixed-width flow diagrams
  // on phones) scrolls sideways on its own instead of widening the page.
  function fitWide(){
    var ch = current.ch;
    if(!ch || !ch.prose) return;
    [].forEach.call(ch.prose.children, function(n){
      if(n.classList.contains('jx-off') || n.offsetParent === null) return;
      // Diagram cards with a scaler size themselves; other cards scroll
      // inside their body so the card frame stays whole. Tables already scroll.
      if(n.classList.contains('jsw-interactive-card')){
        if(n.querySelector('.jsw-diagram-scaler')) return;
        n = n.querySelector(':scope > .jsw-card-body') || n;
      }
      var had = n.classList.contains('jx-scroll-x');
      if(!had && getComputedStyle(n).overflowX !== 'visible') return;
      if(had) n.classList.remove('jx-scroll-x');
      if(n.scrollWidth > n.clientWidth + 4) n.classList.add('jx-scroll-x');
    });
  }
  var fitTimer = null;
  window.addEventListener('resize', function(){ clearTimeout(fitTimer); fitTimer = setTimeout(fitWide, 150); }, { passive: true });

  // A search hit opens its page and brings the smallest visible block that
  // holds the term into view.
  function revealQuery(page, q){
    var ch = page.ch;
    var scope = ch.pageable && !ch.full ? page.nodes : [ch.section];
    var hit = null;
    for(var i = 0; i < scope.length && !hit; i++){
      if((scope[i].textContent || '').toLowerCase().indexOf(q) !== -1) hit = scope[i];
    }
    if(!hit) return;
    var next;
    do{
      next = null;
      for(var k = 0; k < hit.children.length; k++){
        var c = hit.children[k];
        if(c.offsetParent !== null && (c.textContent || '').toLowerCase().indexOf(q) !== -1){ next = c; break; }
      }
      if(next) hit = next;
    } while(next);
    setTimeout(function(){
      jumpY(docTop(hit) - headOffset() - 8);
      replay(hit, 'jx-hit');
      setTimeout(function(){ hit.classList.remove('jx-hit'); }, 2000);
    }, REDUCED ? 0 : 420);
  }

  // hashchange covers links, typed URLs and back/forward between entries
  // (listening to popstate as well would render every hash change twice).
  window.addEventListener('hashchange', function(){ route({}); });

  // In-content links to #ids keep working through the router.
  doc.addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if(a && !e.defaultPrevented){
      var id = a.getAttribute('href').slice(1);
      if(id && (pageIndex[id] || doc.getElementById(id))){ e.preventDefault(); go(id); }
      return;
    }
    var t = e.target.closest ? e.target.closest('[data-go],[data-action],[data-crumb]') : null;
    if(!t) return;
    if(t.hasAttribute('data-go')) go(t.getAttribute('data-go'));
    else if(t.hasAttribute('data-crumb')) go(t.getAttribute('data-crumb'));
    else action(t.getAttribute('data-action'));
  });

  function action(name){
    if(name === 'search') openSearch();
    else if(name === 'close-search') closeSearch();
    else if(name === 'print') window.print();
    else if(name === 'open-nav') openNav();
    else if(name === 'close-nav') closeNav();
  }

  // Scroll spy for full chapters and chapters read as one page.
  var spyTick = false;
  window.addEventListener('scroll', function(){
    if(spyTick) return;
    spyTick = true;
    requestAnimationFrame(function(){
      spyTick = false;
      progress();
      root.classList.toggle('jx-scrolled', window.pageYOffset > 4);
      var ch = current.ch;
      if(!ch || (ch.pageable && !ch.full)) return;
      var list = ch.pageable ? ch.pages.filter(function(p){ return !p.lead; }).map(function(p){ return p.id; }) : ch.jumps.map(function(j){ return j.id; });
      var line = headOffset() + 40, cur = null;
      list.forEach(function(id){ var n = doc.getElementById(id); if(n && n.getBoundingClientRect().top <= line) cur = id; });
      paintNav(current.page, cur);
      if(ch.chipRefs){
        Object.keys(ch.chipRefs).forEach(function(id){ ch.chipRefs[id].classList.toggle('is-page', id === cur); });
      }
    });
  }, { passive: true });

  // Keyboard: ⌘K / Ctrl+K or "/" to search, ← → to turn pages.
  doc.addEventListener('keydown', function(e){
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName || '') || (e.target && e.target.isContentEditable);
    if((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')){ e.preventDefault(); palette.hidden ? openSearch() : closeSearch(); return; }
    if(e.key === 'Escape'){ if(!palette.hidden) closeSearch(); else closeNav(); return; }
    if(typing || !palette.hidden || e.metaKey || e.ctrlKey || e.altKey) return;
    if(e.key === '/'){ e.preventDefault(); openSearch(); return; }
    if(!current.page) return;
    var n = neighbours(current.page);
    if(e.key === 'ArrowRight' && n.next) go(n.next.alias || n.next.id);
    if(e.key === 'ArrowLeft' && n.prev) go(n.prev.alias || n.prev.id);
  });

  /* ---------------------------------------------------- 5 home (filters + cards) */
  var seg = $('#jxSeg'), segInd = $('.jx-seg-ind', seg), cardsBox = $('#jxCards');
  var segBtns = [];

  (function buildHome(){
    var all = el('button', null, 'All');
    all.type = 'button';
    all.setAttribute('role', 'tab');
    all.dataset.group = '-1';
    seg.appendChild(all);
    segBtns.push(all);
    groups.forEach(function(g){
      if(!g.chapters.length) return;
      var b = el('button', null, esc(g.short));
      b.type = 'button';
      b.setAttribute('role', 'tab');
      b.title = g.full;
      b.dataset.group = String(g.idx);
      seg.appendChild(b);
      segBtns.push(b);
    });
    seg.addEventListener('click', function(e){
      var b = e.target.closest('button');
      if(b) filter(+b.dataset.group);
    });

    var i = 0;
    chapters.forEach(function(ch){
      var n = ch.pageable ? ch.pages.filter(function(p){ return !p.lead; }).length : ch.jumps.length;
      var meta = esc(ch.group.short) + (n ? ' · ' + n + ' sections' : '');
      var card = el('button', 'jx-card',
        '<div class="jx-card-top"><span class="jx-card-num">' + esc(ch.num) + '</span><span class="jx-card-go">' + ICON_NEXT + '</span></div>' +
        '<span class="jx-card-title">' + esc(ch.label) + '</span>' +
        '<span class="jx-card-meta">' + meta + '</span>');
      card.type = 'button';
      card.dataset.group = String(ch.group.idx);
      card.style.setProperty('--i', i++);
      card.addEventListener('click', function(){ go(ch.pages[0].alias || ch.pages[0].id); });
      cardsBox.appendChild(card);
    });
    filter(-1, true);
  })();

  function filter(groupIdx, instant){
    segBtns.forEach(function(b){ b.setAttribute('aria-selected', String(+b.dataset.group === groupIdx)); });
    var on = segBtns.filter(function(b){ return +b.dataset.group === groupIdx; })[0];
    moveInd(on, instant);
    var k = 0;
    $$('.jx-card', cardsBox).forEach(function(c){
      var show = groupIdx === -1 || +c.dataset.group === groupIdx;
      c.classList.toggle('is-out', !show);
      if(show){ c.style.setProperty('--i', k++); }
    });
    if(!instant) replay(homeEl, 'jx-play');
  }
  function moveInd(btn, instant){
    if(!btn) return;
    if(instant) segInd.style.transition = 'none';
    var track = seg.scrollWidth;
    segInd.style.width = track + 'px';
    segInd.style.clipPath = 'inset(0 ' + (track - btn.offsetLeft - btn.offsetWidth) + 'px 0 ' + btn.offsetLeft + 'px round 999px)';
    if(instant){ void segInd.offsetWidth; segInd.style.transition = ''; }
    if(btn.scrollIntoView && !wide.matches){
      seg.scrollTo({ left: Math.max(0, btn.offsetLeft - (seg.clientWidth - btn.offsetWidth) / 2), behavior: instant || REDUCED ? 'auto' : 'smooth' });
    }
  }
  window.addEventListener('resize', function(){
    var on = segBtns.filter(function(b){ return b.getAttribute('aria-selected') === 'true'; })[0];
    moveInd(on, true);
  }, { passive: true });
  // fonts change button widths after first paint
  if(doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function(){
    var on = segBtns.filter(function(b){ return b.getAttribute('aria-selected') === 'true'; })[0];
    moveInd(on, true);
  });

  /* ---------------------------------------------------- 6 search palette */
  var palette = $('#jxPalette'), input = $('#jxSearchInput'), results = $('#jxResults');
  var HINT = results.getAttribute('data-hint'), EMPTY = results.getAttribute('data-empty');
  var index = null, hits = [], sel = 0, lastFocus = null;

  // Text with a space at block/cell boundaries so table cells don't run together.
  var BLOCK = /^(P|DIV|LI|TD|TH|TR|H[1-6]|BR|UL|OL|TABLE|SECTION|BUTTON|BLOCKQUOTE)$/;
  function textOf(node){
    var out = [];
    (function walk(n){
      if(n.nodeType === 3){ out.push(n.nodeValue); return; }
      if(n.nodeType !== 1 || n.tagName === 'SCRIPT' || n.tagName === 'STYLE') return;
      var block = BLOCK.test(n.tagName);
      if(block) out.push(' ');
      for(var c = n.firstChild; c; c = c.nextSibling) walk(c);
      if(block) out.push(' ');
    })(node);
    return out.join('');
  }

  function buildIndex(){
    index = [];
    chapters.forEach(function(ch){
      ch.pages.forEach(function(p){
        var text = p.nodes ? p.nodes.map(textOf).join(' ') : textOf(ch.section);
        text = text.replace(/\s+/g, ' ').trim();
        index.push({
          page: p,
          title: p.lead ? ch.title : p.label,
          num: p.lead ? ch.num : p.num,
          crumb: (p.lead ? ch.group.full : ch.num + ' · ' + ch.title),
          text: text, lower: text.toLowerCase(),
          key: ((p.lead ? ch.label + ' ' + ch.title : p.label) + '').toLowerCase()
        });
      });
    });
  }

  function mark(s, q){
    var i = s.toLowerCase().indexOf(q);
    if(i < 0) return esc(s);
    return esc(s.slice(0, i)) + '<mark>' + esc(s.slice(i, i + q.length)) + '</mark>' + esc(s.slice(i + q.length));
  }

  function runSearch(){
    var raw = input.value.trim(), q = raw.toLowerCase();
    results.innerHTML = '';
    hits = []; sel = 0;
    if(!q){ results.appendChild(el('div', 'jx-results-hint', esc(HINT))); return; }
    if(!index) buildIndex();
    var titles = [], texts = [];
    index.forEach(function(r){
      if(r.key.indexOf(q) !== -1) titles.push(r);
      else if(r.lower.indexOf(q) !== -1) texts.push(r);
    });
    if(!titles.length && !texts.length){
      results.appendChild(el('div', 'jx-results-hint', esc(EMPTY.replace('{q}', raw))));
      return;
    }
    var n = 0;
    function section(label, list, withSnippet){
      if(!list.length) return;
      results.appendChild(el('div', 'jx-results-label', esc(label)));
      list.slice(0, 30).forEach(function(r){
        var html = '<span class="jx-result-t">' + (r.num ? '<b>' + esc(r.num) + '</b>' : '') + mark(r.title, q) + '</span>' +
                   '<span class="jx-result-c">' + esc(r.crumb) + '</span>';
        if(withSnippet){
          var i = r.lower.indexOf(q), a = Math.max(0, i - 60), b = Math.min(r.text.length, i + q.length + 90);
          html += '<span class="jx-result-s">' + (a > 0 ? '…' : '') + mark(r.text.slice(a, b), q) + (b < r.text.length ? '…' : '') + '</span>';
        }
        var btn = el('button', 'jx-result', html);
        btn.type = 'button';
        btn.setAttribute('role', 'option');
        btn.style.setProperty('--i', Math.min(n, 12));
        var at = n++;
        btn.addEventListener('click', function(){ pick(at); });
        btn.addEventListener('mousemove', function(){ if(sel !== at){ sel = at; paintSel(); } });
        results.appendChild(btn);
        hits.push({ r: r, btn: btn, q: withSnippet ? q : '' });
      });
    }
    section('Chapters & sections', titles, false);
    section('In the text', texts, true);
    paintSel();
  }
  function paintSel(){
    hits.forEach(function(h, i){ h.btn.classList.toggle('is-on', i === sel); h.btn.setAttribute('aria-selected', String(i === sel)); });
    if(hits[sel] && hits[sel].btn.scrollIntoView) hits[sel].btn.scrollIntoView({ block: 'nearest' });
  }
  function pick(i){
    var h = hits[i];
    if(!h) return;
    closeSearch(true);
    var p = h.r.page;
    go(p.alias || p.id, h.q ? { query: h.q } : {});
  }

  function openSearch(){
    closeNav();
    lastFocus = doc.activeElement;
    palette.hidden = false;
    root.classList.add('jx-lock');
    paintTabs('search');
    runSearch();
    setTimeout(function(){ input.focus(); input.select(); }, 20);
  }
  function closeSearch(silent){
    if(palette.hidden) return;
    palette.hidden = true;
    root.classList.remove('jx-lock');
    paintTabs(current.page ? null : 'home');
    if(!silent && lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  input.addEventListener('input', runSearch);
  input.addEventListener('keydown', function(e){
    if(e.key === 'ArrowDown'){ e.preventDefault(); if(hits.length){ sel = (sel + 1) % hits.length; paintSel(); } }
    else if(e.key === 'ArrowUp'){ e.preventDefault(); if(hits.length){ sel = (sel - 1 + hits.length) % hits.length; paintSel(); } }
    else if(e.key === 'Enter'){ e.preventDefault(); pick(sel); }
  });
  palette.addEventListener('click', function(e){ if(e.target === palette) closeSearch(); });

  /* ------------------------------------- 7 phone sheet, tab bar, progress */
  var tabbar = $('#jxTabbar'), progBar = $('#jxProgress');

  function openNav(){
    if(wide.matches) return;
    root.classList.add('jx-nav-open', 'jx-lock');
    paintTabs('contents');
    var act = $('.jx-nav-sub.is-page', navList) || $('.jx-nav-item.is-active', navList);
    if(act) setTimeout(function(){ act.scrollIntoView({ block: 'center' }); }, 60);
  }
  function closeNav(){
    if(!root.classList.contains('jx-nav-open')) return;
    root.classList.remove('jx-nav-open');
    if(palette.hidden) root.classList.remove('jx-lock');
    paintTabs(current.page ? null : 'home');
  }
  $('#jxScrim').addEventListener('click', closeNav);
  wide.addEventListener && wide.addEventListener('change', function(){ closeNav(); });

  function paintTabs(on){
    $$('button', tabbar).forEach(function(b){ b.classList.toggle('is-on', b.getAttribute('data-tab') === on); });
  }

  function progress(){
    var max = doc.documentElement.scrollHeight - window.innerHeight;
    var p = max > 0 ? Math.min(1, window.pageYOffset / max) : 0;
    progBar.style.transform = 'scaleX(' + p.toFixed(4) + ')';
  }

  // The tab bar steps aside while reading down and returns on the way up.
  var lastY = window.pageYOffset, tabTick = false;
  window.addEventListener('scroll', function(){
    if(tabTick) return;
    tabTick = true;
    requestAnimationFrame(function(){
      tabTick = false;
      var y = window.pageYOffset;
      if(Math.abs(y - lastY) < 8) return;
      var nearEnd = y + window.innerHeight >= doc.documentElement.scrollHeight - 80;
      tabbar.classList.toggle('is-hidden', y > lastY && y > 200 && !nearEnd);
      lastY = y;
    });
  }, { passive: true });

  /* ----------------------------------------------- 8 compat globals + boot */
  // Names the manual's content and older links call.
  window.scrollToSection = function(id, e){ if(e && e.preventDefault) e.preventDefault(); go(id); };
  window.goHome = function(){ go('home'); };
  window.goToView = function(i){ var c = chapters[i]; if(c) go(c.pages[0].alias || c.pages[0].id); else go('home'); };
  window.openSearch = openSearch;
  window.closeSearch = closeSearch;
  window.toggleSearchModal = function(force){ var open = force !== undefined ? force : palette.hidden; open ? openSearch() : closeSearch(); };

  // Annexure template cards (message text carried over from the manual portal).
  var toast = $('#jxToast'), toastTimer = null;
  window.handleAnnexDownload = function(e, title){
    if(e && e.preventDefault) e.preventDefault();
    toast.innerHTML = '<span style="font-size:18px;">📁</span> <span>Template file <strong>' + esc(title) + '</strong> will be downloadable once final document attachments are linked.</span>';
    toast.classList.add('is-on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function(){ toast.classList.remove('is-on'); }, 3800);
  };

  if('scrollRestoration' in history) history.scrollRestoration = 'manual';
  route({ inPlace: true });
})();
