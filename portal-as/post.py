"""Whole-page post-processing for service.html (openers, Principles cards, emphasis, annexure chips, brand)."""
import re
import asdoc  # noqa
import build as B

AS_CSS = '''<style id="as-css2">
.as-ind{margin:18px 0}
.as-ind-root{background:#1b1b1d;color:#fff;border-radius:12px;padding:14px 18px;text-align:center;max-width:520px;margin:0 auto 16px}
.as-ind-root h4{margin:0;font-size:19px;color:#fff}
.as-ind-root p{margin:2px 0 0;font-size:13.5px;color:rgba(255,255,255,.78)}
.as-ind-cols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;align-items:start}
.as-ind-head{background:#e6e6e8;border:1.5px solid #8d8d92;border-radius:12px;padding:12px 14px;text-align:center;position:relative}
.as-ind-head h4{margin:0;font-size:17px}
.as-ind-head em{display:block;font-size:13.5px;color:#46474c}
.as-ind-head b{display:block;font-size:13.5px}
.as-ind-n{position:absolute;left:10px;top:10px;width:24px;height:24px;border-radius:50%;background:#1b1b1d;color:#fff;font-size:12px;font-weight:700;display:grid;place-items:center}
.as-ind-box{margin-top:10px;margin-left:14px;background:#fff;border:1.5px solid #b4b4b8;border-radius:10px;padding:10px 14px}
.as-ind-box h5{margin:0 0 6px;font-size:15px}
.as-ind-box ul{margin:0;padding-left:18px;font-size:13.5px;line-height:1.5}
@media(max-width:860px){.as-ind-cols{grid-template-columns:1fr}}
.as-levels{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:14px 0 8px}
.as-level{border:1px solid rgba(0,0,0,.14);border-top:4px solid #151515;border-radius:12px;background:rgba(255,255,255,.72);padding:16px 18px}
.as-level-h{display:flex;align-items:center;gap:10px}
.as-level-h h4{margin:0;font-size:18px}
.as-level-n{width:30px;height:30px;border-radius:50%;background:#151515;color:#fff;display:grid;place-items:center;font-weight:700;font-size:14px}
.as-level-d{font-size:14px;margin:10px 0 8px}
.as-level-l{margin:0;padding-left:0;list-style:none;display:grid;gap:6px}
.as-level-l li{font-size:14.5px;font-weight:600;padding:7px 10px;background:rgba(0,0,0,.05);border-radius:8px}
.as-level-l li::before{content:attr(value) ". ";font-variant-numeric:tabular-nums}
@media(max-width:860px){.as-levels{grid-template-columns:1fr}}
.as-note{font-size:14px;margin-top:10px}
.pr-grid.pr-n5{grid-template-columns:repeat(3,1fr)}
.rd-detail .chip{text-transform:none}
.fx-lj-body{text-align:left;display:flex;flex-direction:column;gap:8px}
.as-lj-when{font-weight:700;font-size:15px}
.as-lj-obj{font-size:13.5px;font-weight:500;line-height:1.5}
.as-theme{margin:6px 0 0;font-weight:700;font-size:14px}
.as-tg th,.as-tg td{text-align:center;vertical-align:middle}
.as-tg-r{background:#151515!important;color:#fff!important;width:90px}
.as-tg-c{font-weight:600}
.as-tg-0{background:#f1f1f2}.as-tg-1{background:#e1e1e4}.as-tg-2{background:#c9c9ce}.as-tg-3{background:#a9a9b0}.as-tg-4{background:#8b8b93;color:#fff}
.as-attr{margin:14px 0;display:grid;gap:12px}
.as-attr-f{display:flex;flex-wrap:wrap;gap:10px;align-items:center;background:#151515;color:#fff;border-radius:12px;padding:16px 20px;font-size:17px;font-weight:700}
.as-attr-f b{opacity:.7}
.as-attr-n{font-size:13.5px;margin:0}
.as-attr-e{border:1px solid rgba(0,0,0,.14);border-left:4px solid #151515;border-radius:12px;background:rgba(255,255,255,.72);padding:14px 18px}
.as-attr-e h5{margin:0 0 8px}
.as-attr-e ul{margin:0;padding-left:18px;line-height:1.7}
.as-attr-r{font-weight:700;font-size:1.05em;list-style:none;margin-left:-18px;margin-top:6px;padding:8px 12px;background:#151515;color:#fff;border-radius:8px}

/* ── Modern 3-Column Grid for Intro Principles ── */
.ig-pr.ig-pr-3cols {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 16px !important;
  margin: 22px 0 34px !important;
  max-width: 100% !important;
}
.ig-pr.ig-pr-3cols .ig-pr-card {
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  border-radius: 16px !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
  background: #ffffff !important;
}
.ig-pr.ig-pr-3cols .ig-pr-card ul.list-clean {
  flex: 1 !important;
  padding: 20px 22px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 10px !important;
}
.ig-pr.ig-pr-3cols .ig-pr-card ul.list-clean li {
  font-size: 14px !important;
  line-height: 1.55 !important;
  color: #2c2c2e !important;
}
@media (max-width: 960px) {
  .ig-pr.ig-pr-3cols {
    grid-template-columns: 1fr !important;
  }
}

/* ── SMART KPI & Goals Cascade Infographic ── */
.as-smart-card {
  margin: 28px 0 36px !important;
  border: 1px solid rgba(0, 0, 0, 0.09) !important;
  border-radius: 18px !important;
  background: #ffffff !important;
  overflow: hidden !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
}
.as-goal-block {
  padding: 24px 28px !important;
}
.as-goal-dealership {
  background: #fafafb !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}
.as-goal-sa {
  background: #ffffff !important;
}
.as-goal-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  margin-bottom: 14px !important;
  flex-wrap: wrap !important;
  gap: 10px !important;
}
.as-goal-badge {
  display: inline-flex !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 6px 14px !important;
  background: #151517 !important;
  color: #ffffff !important;
  border-radius: 20px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
}
.as-goal-badge svg {
  stroke: #ffffff !important;
}
.as-goal-badge.as-badge-role {
  background: #2c2c2e !important;
}
.as-goal-text {
  font-size: 15px !important;
  line-height: 1.65 !important;
  color: #2c2c2e !important;
  margin: 0 !important;
}
.as-goal-text strong {
  color: #111113 !important;
  font-weight: 750 !important;
}
.as-goal-cascade {
  position: relative !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 9px 0 !important;
  background: #f0f0f3 !important;
  border-top: 1px dashed rgba(0, 0, 0, 0.12) !important;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.12) !important;
}
.as-cascade-pill {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 5px 16px !important;
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  border-radius: 20px !important;
  font-size: 11.5px !important;
  font-weight: 700 !important;
  color: #1c1c1e !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
}
.as-smart-breakdown {
  padding: 24px 28px !important;
  background: #111113 !important;
  color: #ffffff !important;
}
.as-smart-heading {
  display: flex !important;
  align-items: baseline !important;
  justify-content: space-between !important;
  margin-bottom: 20px !important;
  padding-bottom: 12px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
}
.as-smart-title {
  font-size: 18px !important;
  font-weight: 800 !important;
  letter-spacing: -0.01em !important;
  color: #ffffff !important;
}
.as-smart-tag {
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  color: rgba(255, 255, 255, 0.6) !important;
}
.as-smart-grid {
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
}
.as-smart-item {
  display: flex !important;
  align-items: flex-start !important;
  gap: 16px !important;
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
  padding: 14px 18px !important;
  transition: background 0.2s !important;
}
.as-smart-item:hover {
  background: rgba(255, 255, 255, 0.09) !important;
}
.as-smart-letter {
  flex-shrink: 0 !important;
  width: 38px !important;
  height: 38px !important;
  border-radius: 10px !important;
  background: #ffffff !important;
  color: #111113 !important;
  font-size: 18px !important;
  font-weight: 900 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}
.as-smart-content {
  flex: 1 !important;
}
.as-smart-name {
  font-size: 14.5px !important;
  font-weight: 750 !important;
  color: #ffffff !important;
  margin-bottom: 3px !important;
  letter-spacing: -0.01em !important;
}
.as-smart-text {
  font-size: 13.5px !important;
  line-height: 1.5 !important;
  color: rgba(255, 255, 255, 0.82) !important;
  margin: 0 !important;
}
.as-smart-text strong {
  color: #ffffff !important;
  font-weight: 700 !important;
}

@media (max-width: 860px) {
  .as-kpi-metrics-grid {
    grid-template-columns: 1fr !important;
  }
  .as-goal-block, .as-smart-breakdown {
    padding: 18px 20px !important;
  }
}

/* ── Modern macOS Mail Template Card ── */
.as-email-card {
  margin: 28px 0 34px !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  border-radius: 16px !important;
  background: #ffffff !important;
  overflow: hidden !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05) !important;
}
.as-email-window-bar {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 12px 18px !important;
  background: #f2f2f4 !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.07) !important;
}
.as-win-dot {
  width: 11px !important;
  height: 11px !important;
  border-radius: 50% !important;
}
.as-win-red { background: #ff5f56 !important; }
.as-win-yel { background: #ffbd2e !important; }
.as-win-grn { background: #27c93f !important; }
.as-win-title {
  margin-left: 10px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  color: #636366 !important;
}
.as-email-headers {
  padding: 16px 22px !important;
  background: #fafafb !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 8px !important;
  font-size: 13.5px !important;
}
.as-email-hdr-row {
  display: flex !important;
  align-items: baseline !important;
  gap: 12px !important;
}
.as-hdr-lbl {
  width: 65px !important;
  font-weight: 700 !important;
  color: #8e8e93 !important;
  text-transform: uppercase !important;
  font-size: 11.5px !important;
  letter-spacing: 0.04em !important;
}
.as-hdr-val {
  color: #1c1c1e !important;
  font-weight: 550 !important;
}
.as-email-body {
  padding: 24px 28px !important;
  font-size: 14.5px !important;
  line-height: 1.65 !important;
  color: #2c2c2e !important;
}
.as-email-section-title {
  font-weight: 750 !important;
  color: #111113 !important;
  margin: 16px 0 6px !important;
  font-size: 14.5px !important;
}

/* ── Perks ── */
.as-perks-container {
  margin: 24px 0 30px !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  border-radius: 16px !important;
  background: #ffffff !important;
  padding: 20px 24px !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
}
.as-perks-header {
  margin-bottom: 16px !important;
}
.as-perks-badge {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  font-size: 13.5px !important;
  font-weight: 750 !important;
  color: #111113 !important;
}
.as-perks-grid {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 14px !important;
}
.as-perk-item {
  display: flex !important;
  align-items: center !important;
  gap: 14px !important;
  padding: 14px 16px !important;
  border-radius: 12px !important;
  background: #fafafb !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}
.as-perk-icon {
  width: 38px !important;
  height: 38px !important;
  border-radius: 10px !important;
  background: #151517 !important;
  color: #ffffff !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
}
.as-perk-icon svg { stroke: #ffffff !important; }
.as-perk-text {
  display: flex !important;
  flex-direction: column !important;
  gap: 2px !important;
}
.as-perk-text strong {
  font-size: 14px !important;
  color: #111113 !important;
}
.as-perk-text span {
  font-size: 12px !important;
  color: #636366 !important;
  line-height: 1.35 !important;
}

/* ── IJP ── */
.as-ijp-container {
  margin: 24px 0 32px !important;
}
.as-ijp-grid {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 16px !important;
}
.as-ijp-box {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.09) !important;
  border-radius: 16px !important;
  padding: 20px 22px !important;
  display: flex !important;
  flex-direction: column !important;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03) !important;
}
.as-ijp-title {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  margin-bottom: 14px !important;
}
.as-ijp-step {
  width: 28px !important;
  height: 28px !important;
  border-radius: 8px !important;
  background: #111113 !important;
  color: #ffffff !important;
  font-size: 12px !important;
  font-weight: 800 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.as-ijp-title h4 {
  margin: 0 !important;
  font-size: 16px !important;
  font-weight: 750 !important;
  color: #111113 !important;
}
.as-ijp-box ul.list-clean {
  flex: 1 !important;
  margin: 0 0 10px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 8px !important;
  font-size: 13.5px !important;
  line-height: 1.5 !important;
}
.as-ijp-note {
  font-size: 12px !important;
  font-style: italic !important;
  color: #636366 !important;
  margin-top: auto !important;
  padding-top: 10px !important;
  border-top: 1px dashed rgba(0, 0, 0, 0.1) !important;
}
.as-ijp-tag {
  display: inline-block !important;
  padding: 6px 12px !important;
  background: #111113 !important;
  color: #ffffff !important;
  font-size: 11.5px !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  margin-top: auto !important;
}

@media (max-width: 860px) {
  .as-perks-grid, .as-ijp-grid {
    grid-template-columns: 1fr !important;
  }
}

/* ── Modern Avatars & Role Directory Polish ── */
.rd-avatar-sm {
  width: 38px !important;
  height: 38px !important;
  border-radius: 50% !important;
  border: 1.5px solid rgba(0, 0, 0, 0.12) !important;
  object-fit: cover !important;
  object-position: center top !important;
  filter: grayscale(100%) contrast(1.08) !important;
  transition: transform 0.2s, border-color 0.2s !important;
  background: #f0f0f2 !important;
}
.rd-role-btn:hover .rd-avatar-sm {
  transform: scale(1.08);
  border-color: #111113 !important;
}
.rd-role-btn.active .rd-avatar-sm {
  border: 2px solid #ffffff !important;
  box-shadow: 0 0 0 2px #111113 !important;
  transform: scale(1.1);
}
.rd-avatar-lg {
  width: 84px !important;
  height: 84px !important;
  border-radius: 50% !important;
  border: 2.5px solid #111113 !important;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
  object-fit: cover !important;
  object-position: center top !important;
  filter: grayscale(100%) contrast(1.1) !important;
  background: #f0f0f2 !important;
}
</style>'''


def reorder(h):
    """Chapter openers: Objective/Purpose first, then the Benefit lists side by side, then Principles as its own sub-heading."""
    row_re = re.compile(r'<div class="meta-row reveal"[^>]*>')
    out, pos, n = [], 0, 0
    for m in row_re.finditer(h):
        if m.start() < pos:
            continue
        end = B._div_end(h, m.start())
        items = re.findall(r'<div class="meta-item">.*?</div>', h[m.end():end], re.S)
        purpose = [x for x in items if re.search(r'<span class="eyebrow">(Purpose|Objective):?\s*</span>', x, re.I)]
        pr = [x for x in items if re.search(r'<span class="eyebrow">Principles:?\s*</span>', x, re.I)]
        rest = [x for x in items if x not in pr and x not in purpose]
        if not purpose or 'data-solo' in m.group(0):
            continue
        solo = re.sub(r'style="', 'data-solo="1" style="', m.group(0), 1)
        if pr:
            body = re.sub(r'<div class="meta-item"><span class="eyebrow">Principles:?\s*</span>\s*(.*)</div>$', r'\1', pr[0].strip(), flags=re.S | re.I)
            princ = '\n<h3 class="sub-title subhead">Principles</h3>\n' + body
        else:
            princ = ''
        out.append(h[pos:m.start()] + solo + ''.join(purpose) + '</div>\n' + (m.group(0) + ''.join(rest) + '</div>' if rest else '') + princ + '\n')
        pos = end
        n += 1
    out.append(h[pos:])
    print('openers reordered', n)
    return ''.join(out)


def principle_cards(h):
    def cards(m):
        items = re.findall(r'<li>(.*?)</li>', m.group(2), re.S)
        c = ''.join(f'<li class="pr-card"><span class="pr-num">{i:02d}</span><p>{t.strip()}</p></li>' for i, t in enumerate(items, 1))
        return f'{m.group(1)}<ol class="pr-grid pr-n{len(items)}">{c}</ol>'
    return re.sub(r'(<h3 class="sub-title subhead">Principles</h3>\s*)<ul class="list-clean"[^>]*>((?:(?!</ul>).)*?)</ul>', cards, h, flags=re.S)


def region(h):
    a = h.find('    <article class="jx-chapter" id="chap-fm-i"')
    e = h.find('</article>', h.find('id="chap-annexure"')) + len('</article>')
    return a, e


def run(h):
    a, e = region(h)
    reg = reorder(h[a:e])
    reg = re.sub(r'<li>\s*:?\s*</li>\s*', '', reg)
    reg = principle_cards(reg)
    import readability
    strip = lambda x: re.sub(r'<[^>]+>', '', x)
    r2, stats, leads = readability.emphasize(reg)
    assert strip(r2) == strip(reg), 'emphasis changed text'
    print('emphasis', stats)
    reg = r2
    # annexure chips -> the annexure entry
    codes = set(re.findall(r'id="annex-(\d{1,2}[A-Z])"', reg))
    used = set(re.findall(r'<span class="v7-ref">(\d{1,2}[A-Z])</span>', reg))
    print('annex chips', len(used), 'missing', sorted(used - codes))
    reg = re.sub(r'<span class="v7-ref">(\d{1,2}[A-Z])</span>',
                 lambda m: f'<a class="v7-ref" href="#annex-{m.group(1)}">{m.group(1)}</a>' if m.group(1) in codes else m.group(0), reg)
    h = h[:a] + reg + h[e:]
    h = h.replace('</head>', AS_CSS + '</head>', 1)
    return h
