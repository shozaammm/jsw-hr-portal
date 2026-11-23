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


def annex_item(code, name):
    title = f'{code}. {name}'
    return (f'<div class="annex-file-item as-annex-item" id="annex-{code}" title="{escq(title)}">'
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


TOC_GROUPS = [
    ('Introduction', ['fm-i', 'fm-ii', 'fm-iii']),
    ('Manpower Planning and Selection', ['ch2', 'ch1', 'ch3', 'ch4', 'ch5']),
    ('Manpower Development', ['ch6', 'ch7', 'ch8', 'ch9']),
    ('Manpower Governance', ['ch10', 'ch11', 'ch12']),
    ('Leadership', ['ch13']),
    ('Annexure', ['annexure']),
]
TITLES = {
    'fm-i': ('i', 'Foreword'), 'fm-ii': ('ii', 'JSW Group and JSW Motors Vision and Foundation'),
    'fm-iii': ('iii', 'HR Systems at a Glance'),
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
    h = h.replace('</head>', AS_CSS + '</head>', 1)
    return h
