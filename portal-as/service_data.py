"""Service-manual data and shell patches (org charts, TOC, brand, annexure list)."""
import html, json, re

esc = lambda s: html.escape(s, quote=False)
escq = lambda s: html.escape(s, quote=True)

# ───────────── org charts: transcribed from the three pictures in chapter 1 of the docx ─────────────
# basis: dp = "Per DP" (green), outlet = "Per Outlet" (pink), volume = "Volume Based" (yellow); star = "3S | Can be Common, 2S | as per requirement"
def N(name, basis, *kids, star=False):
    d = {'name': name, 'basis': basis, 'children': list(kids)}
    if star:
        d['star'] = True
    return d


def _service_block(controller_kids=True, qc=True):
    wc_kids = [N('Diagnostic Expert (DE)', 'outlet'), N('Service Technician', 'volume')]
    if qc:
        wc_kids.append(N('Quality Controller / Road tester', 'outlet'))
    wc_kids.append(N('Washing Supervisor', 'outlet', N('Washer', 'volume')))
    return N('Service Manager', 'outlet',
             N('Workshop Controller', 'outlet', *wc_kids),
             N('Service Advisor', 'volume'),
             N('Warranty Specialist', 'outlet'),
             N('PDI In-charge', 'outlet', N('Technician — PDI &Axs', 'volume')))


def _crm(marketing=True):
    kids = [N('CRE Service', 'volume')]
    if marketing:
        kids.append(N('Service Marketing Executive', 'outlet'))
    kids.append(N('Service Reception Co-Ordinator', 'outlet',
                  N('Housekeeping (SR)', 'outlet', star=True), N('Pantry Team', 'outlet', star=True)))
    kids.append(N('P&D Drivers', 'volume'))
    return N('CRM Service', 'outlet', *kids)


def _gm_tree(top, finance):
    return N(top, 'dp',
             N(finance, 'dp', N('Accountant', 'outlet', star=True), N('Cashier', 'outlet', star=True)),
             N('General Manager - Service', 'dp',
               _service_block(),
               N('Bodyshop Manager', 'outlet',
                 N('Bodyshop SA', 'volume'),
                 N('Bodyshop Controller', 'volume', N('Body Technician', 'volume'), N('Paint Technician', 'volume'),
                   N('Service Technician (Body Shop)', 'volume'))),
               N('Parts Manager', 'outlet', N('Parts Executive', 'volume')),
               _crm()),
             N('HR Manager', 'dp', N('HR Executive/Admin', 'dp'), N('Security', 'outlet', star=True)))


ORG = [
    {'label': 'XPlus & X Category', 'tree': _gm_tree('Business Head / CEO', 'CFO'),
     'coord': [{'from': 'HR Manager', 'to': 'General Manager - Service'}]},
    {'label': 'Y Category', 'tree': _gm_tree('Business Head / CEO', 'Accounts & Finance Head'),
     'coord': [{'from': 'HR Manager', 'to': 'General Manager - Service'}]},
    {'label': 'Z Category', 'tree': N('Dealer Principal', 'dp',
        N('Accounts & Finance Head', 'dp', N('Accountant', 'outlet', star=True), N('Cashier', 'outlet', star=True)),
        N('Service Manager', 'outlet',
          N('Workshop Controller', 'outlet', N('Diagnostic Expert (DE)', 'outlet'), N('Service Technician', 'volume'),
            N('Washing Supervisor', 'outlet', N('Washer', 'volume'))),
          N('Service Advisor', 'volume'), N('Warranty Specialist', 'outlet'),
          N('PDI In-charge', 'outlet', N('Technician — PDI &Axs', 'volume')),
          N('Bodyshop SA', 'volume'), N('Body Technician', 'volume'), N('Paint Technician', 'volume'),
          N('Service Technician (Body Shop)', 'volume')),
        N('Parts Manager', 'outlet', N('Parts Executive', 'volume')),
        _crm(marketing=False),
        N('HR Manager', 'dp', N('Security', 'outlet', star=True))),
     'coord': []},
]


def tree_html(n):
    cls = 'node norm-' + n['basis']
    star = '<span class="node-star"> ★</span>' if n.get('star') else ''
    s = f'<li><div class="{cls}" data-name="{escq(n["name"])}">{esc(n["name"])}{star}</div>'
    if n['children']:
        s += '<ul>' + ''.join(tree_html(c) for c in n['children']) + '</ul>'
    return s + '</li>'


def tree_stores():
    return ''.join(f'<div class="tree-store" id="orgTreeCat{i}" style="display:none"><ul class="tree">{tree_html(c["tree"])}</ul></div>'
                   for i, c in enumerate(ORG))


def annex_item(code, name, with_id=False):
    title = f'{code}. {name}'
    idattr = f' id="annex-{code}"' if with_id else ''
    return (f'<div class="annex-file-item as-annex-item"{idattr} title="{escq(title)}">'
            f'<div class="annex-file-left"><div class="annex-file-icon">📄</div><div class="annex-file-name">{esc(title)}</div></div></div>')


AS_CSS = '''<style id="as-css">
.as-annex .as-annex-item{cursor:default}
.as-annex .as-annex-item:hover{transform:none;box-shadow:none}
.node-star{font-size:1.1em;margin-left:2px}
.legend-chip .node-star{margin:0 6px 0 0;color:#1b1b1d}
.rd-avatar-sm,.rd-avatar-lg{background:#e4e4e7}
.rd-resp-head{margin:14px 0 4px;font-size:14.5px;font-weight:700;color:var(--ink,#1b1b1d)}
.rd-detail .rd-note{font-size:13px;opacity:.8}
</style>'''


def js(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


TOC_GROUPS = [   # the Contents table of the docx is flat: i-iii, then chapters 1-13
    ('Introduction', ['fm-i', 'fm-ii', 'fm-iii']),
    ('Chapters', ['ch2', 'ch1', 'ch3', 'ch4', 'ch5', 'ch6', 'ch7', 'ch8', 'ch9', 'ch10', 'ch11', 'ch12', 'ch13']),
    ('Annexure', ['annexure']),
]
TITLES = {
    'fm-i': ('i', 'Foreword'), 'fm-ii': ('ii', 'JSW Group and JSW Motors Vision and Foundation'),
    'fm-iii': ('iii', 'How to Read the Manual'),
    'ch2': ('1', 'Dealership Organisation Structure'), 'ch1': ('2', 'Job Descriptions'),
    'ch3': ('3', 'Recruitment and Selection'), 'ch4': ('4', 'Compensation, Benefits and Incentive Policy'),
    'ch5': ('5', 'Joining and Confirmation'), 'ch6': ('6', 'Learning and Development'),
    'ch7': ('7', 'Performance Management'), 'ch8': ('8', 'Career Progression'),
    'ch9': ('9', 'Employee Engagement, Rewards and Recognition'), 'ch10': ('10', 'Discipline and Conduct'),
    'ch11': ('11', 'Employee Exit Management'), 'ch12': ('12', 'Organisation Policies'),
    'ch13': ('13', 'Leadership Practices'), 'annexure': ('', 'Annexures'),
}


def sub_num(label):
    m = re.match(r'^(\d+(?:\.\d+)*)\s+(.*)$', label.strip())
    return (m.group(1), m.group(2)) if m else ('', label.strip())


def build_toc(subs):
    def fix(cid, s):
        out, n = [], 0
        for sid, l in s:
            num, lab = sub_num(l); n += 1
            out.append((sid, l if num else f'{cid[2:]}.{n} {lab}'))
        return out
    parts = []
    for g, ids in TOC_GROUPS:
        items = []
        for cid in ids:
            num, label = TITLES[cid]
            line = f"    {{id:'{cid}', num:'{num}', label:'{js(label)}', live:true"
            if cid in subs and subs[cid]:
                line += ', subs:[\n' + ',\n'.join(
                    f"      {{id:'{sid}', num:'{sub_num(l)[0]}', label:'{js(sub_num(l)[1])}'}}" for sid, l in fix(cid, subs[cid])) + '\n    ]'
            items.append(line + '}')
        parts.append(f"  {{group:'{g}', items:[\n" + ',\n'.join(items) + '\n  ]}')
    return 'window.JX_TOC = [\n' + ',\n'.join(parts) + ',\n];'


def patch_shell(h, subs):
    # TOC
    a = h.find('window.JX_TOC = ['); b = h.find('];', a) + 2
    h = h[:a] + build_toc(subs) + h[b:]
    # org-chart data
    a = h.find('window.ORG_CATEGORIES = [')
    b = h.find('];\n      var currentOrgCategory', a)
    assert a > 0 and b > a
    h = h[:a] + 'window.ORG_CATEGORIES = ' + json.dumps(ORG, ensure_ascii=False) + h[b + 1:]
    # star + legend
    old = '        div.textContent = node.name;\n'
    assert h.count(old) == 1
    h = h.replace(old, old + "        if(node.star){ var st = document.createElement('span'); st.className = 'node-star'; st.textContent = ' ★'; div.appendChild(st); }\n")
    old = '        legend.innerHTML = html;\n'
    assert h.count(old) == 1
    h = h.replace(old, "        if(treeStr.indexOf('\"star\"') !== -1) html += '<span class=\"legend-chip\"><span class=\"node-star\">★</span>3S | Can be Common, 2S | as per requirement.</span>';\n" + old)
    # annexure documents of the sales manual are not part of this manual
    a = h.find('window.ANNEX_DOCS = ')
    b = h.find('</script>', a)
    h = h[:a] + 'window.ANNEX_DOCS = {};\n' + h[b:]
    # org chart: no split into X / XPlus tabs (the docx has one chart "XPlus & X Category"); download header from the docx picture titles
    sp = "        (function(a){ var x = a[0]; a.splice(0, 1, Object.assign({}, x, {label: 'X Category'}), Object.assign({}, x, {label: 'XPlus Category'})); })(window.ORG_CATEGORIES);\n"
    assert h.count(sp) == 1
    h = h.replace(sp, '')
    old = "JSW MOTORS &#183; DEALERSHIP ORGANISATION STRUCTURE"
    assert h.count(old) == 1
    h = h.replace(old, 'Dealer Service Manpower Organization Chart')
    old = "Recommended Structure: ' + cleanCatLabel + ' &#183; Defined as per volume norms and city category</text>"
    assert h.count(old) == 1
    h = h.replace(old, "' + cleanCatLabel + '</text>")
    # brand: the docx cover is "JSW HR Operations Manual: TRUST"
    h = h.replace('<span>HROS</span>', '<span>HR Operations Manual</span>', 1)
    hero = re.search(r'<h1 class="jx-hero-title">.*?</h1>', h, re.S).group(0)
    pillars = ['<b>T</b>alent Development', '<b>R</b>eliability', '<b>U</b>nified Standards', '<b>S</b>hared Growth', '<b>T</b>eamwork for Customers']
    newhero = ('<h1 class="jx-hero-title"><span class="jx-hero-word" aria-label="TRUST">' + ''.join(f'<span aria-hidden="true" style="--i:{i}">{c}</span>' for i, c in enumerate('TRUST'))
               + '</span><span class="jx-hero-line">JSW HR Operations Manual</span></h1>'
               '\n        <ul class="jx-pillars">' + ''.join(f'<li style="--i:{i}">{p}</li>' for i, p in enumerate(pillars)) + '</ul>'
               '\n        <p class="jx-hero-quote">“Building a dealership network our customers can trust.”</p>')
    h = h.replace(hero, newhero, 1)
    h = h.replace('<p>HROS: Human Resource Operating Standards · Service</p>', '<p>TRUST: JSW HR Operations Manual</p>')
    h = h.replace('<title>JSW HR Operations Manual · Service</title>', '<title>JSW HR Operations Manual: TRUST</title>', 1)
    h = h.replace('across all 26+ JSW policy chapters...', 'the manual...').replace('No matching policies found for', 'No matching results found for')
    h = h.replace('JSW Motors Dealership Operations Manual &middot; Controlled Document', 'JSW HR Operations Manual')
    h = h.replace('</head>', AS_CSS + '</head>', 1)
    return h
