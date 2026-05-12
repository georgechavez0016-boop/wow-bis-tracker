"""
Reads bis_data.json and writes index.html — a self-contained viewer
with no server required. Open the HTML file directly in a browser.
"""
import json
from collections import defaultdict
from datetime import datetime

with open("bis_data.json", encoding="utf-8") as f:
    data = json.load(f)

# Attach competition info to each item
item_competition: dict[int, list] = defaultdict(list)
for spec in data:
    for item in spec["bis_items"]:
        if item["item_id"]:
            item_competition[item["item_id"]].append({
                "class": spec["class"],
                "spec": spec["spec"],
                "role": spec.get("role", "DPS"),
                "slot": item["slot"],
            })

for spec in data:
    for item in spec["bis_items"]:
        if item["item_id"]:
            item["competitors"] = [
                c for c in item_competition[item["item_id"]]
                if not (c["class"] == spec["class"] and c["spec"] == spec["spec"])
            ]
        else:
            item["competitors"] = []

CLASS_COLORS = {
    "Death Knight": "#C41E3A",
    "Demon Hunter": "#A330C9",
    "Druid":        "#FF7C0A",
    "Evoker":       "#33937F",
    "Hunter":       "#AAD372",
    "Mage":         "#3FC7EB",
    "Monk":         "#00FF98",
    "Paladin":      "#F48CBA",
    "Priest":       "#FFFFFF",
    "Rogue":        "#FFF468",
    "Shaman":       "#0070DD",
    "Warlock":      "#8788EE",
    "Warrior":      "#C69B3A",
}

generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
total_specs = len(data)
parsed_specs = sum(1 for s in data if s["bis_items"])
all_parsed = parsed_specs == total_specs
specs_color = "#4caf50" if all_parsed else "#e05252"
specs_label = f"{parsed_specs}/{total_specs} specs parsed"
data_json = json.dumps(data, ensure_ascii=False)
colors_json = json.dumps(CLASS_COLORS, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WoW BiS Competition</title>
<script>const whTooltips = {{colorLinks: false, iconizeLinks: false, renameLinks: false}};</script>
<script src="https://wow.zamimg.com/js/tooltips.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0d0d14;
    color: #e0d9cc;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 14px;
  }}
  header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-bottom: 1px solid #3a3a5c;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }}
  header h1 {{ font-size: 20px; font-weight: 700; color: #f0b932; letter-spacing: 0.5px; }}
  header .updated {{ font-size: 12px; color: #555; margin-left: auto; display: flex; align-items: center; gap: 12px; }}
  header .spec-count {{ font-size: 12px; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid; }}
  .controls {{
    background: #13131f;
    border-bottom: 1px solid #2a2a44;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .role-filters {{ display: flex; gap: 6px; align-items: center; }}
  .role-filters label {{ color: #aaa; font-size: 13px; margin-right: 4px; }}
  .role-btn {{
    padding: 5px 14px;
    border-radius: 4px;
    border: 1px solid #3a3a5c;
    background: #1e1e30;
    color: #888;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  .role-btn:hover {{ border-color: #666; color: #ccc; }}
  .role-btn.active {{ color: #0d0d14; border-color: transparent; }}
  .role-btn[data-role="All"].active   {{ background: #f0b932; color: #0d0d14; }}
  .role-btn[data-role="Tank"].active  {{ background: #4a90d9; }}
  .role-btn[data-role="Healer"].active {{ background: #4caf50; }}
  .role-btn[data-role="DPS"].active   {{ background: #e05252; }}
  .spec-select-wrap {{ display: flex; align-items: center; gap: 8px; }}
  .spec-select-wrap label {{ color: #aaa; font-size: 13px; }}
  select {{
    background: #1e1e30;
    color: #e0d9cc;
    border: 1px solid #3a3a5c;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 14px;
    cursor: pointer;
    min-width: 200px;
  }}
  select:focus {{ outline: none; border-color: #f0b932; }}
  .tab-bar {{
    display: flex;
    gap: 2px;
    padding: 0 24px;
    background: #13131f;
    border-bottom: 1px solid #2a2a44;
  }}
  .tab {{
    padding: 10px 18px;
    cursor: pointer;
    color: #888;
    font-size: 13px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
  }}
  .tab:hover {{ color: #ccc; }}
  .tab.active {{ color: #f0b932; border-bottom-color: #f0b932; }}
  .view {{ display: none; padding: 24px; }}
  .view.active {{ display: block; }}
  table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
  th {{
    background: #1a1a2e;
    color: #aaa;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #2a2a44;
    position: sticky;
    top: 0;
    z-index: 1;
    overflow: hidden;
    white-space: nowrap;
    user-select: none;
  }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #1e1e30; vertical-align: middle; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  td.col-comp {{ white-space: normal; }}
  .col-resizer {{
    position: absolute; right: 0; top: 0; height: 100%;
    width: 5px; cursor: col-resize; z-index: 2;
  }}
  .col-resizer:hover, .col-resizer.dragging {{ background: #f0b932; opacity: 0.8; }}
  tr:hover td {{ background: #181828; }}
  .col-slot   {{ width: 120px; color: #888; font-size: 13px; }}
  .col-source {{ width: 160px; color: #888; font-size: 13px; }}
  .col-comp   {{ width: 280px; }}
  .col-count  {{ width: 60px; text-align: center; }}
  .item-name a {{ text-decoration: none; color: #0070ff; transition: color 0.15s; }}
  .item-name a:hover {{ text-decoration: underline; color: #5ba3ff; }}
  .item-name a.contested {{ color: #ff9b3d; }}
  .badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 7px 2px 4px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px 2px;
    white-space: nowrap;
  }}
  .no-comp {{ color: #444; font-size: 12px; font-style: italic; }}
  .contest-count {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 50%;
    font-size: 11px; font-weight: 700;
  }}
  .hot  {{ background: #4a1010; color: #ff6b6b; }}
  .warm {{ background: #3a2a00; color: #f0b932; }}
  .row-hot  {{ background: #1a0a0a !important; }}
  .row-warm {{ background: #141020 !important; }}
  .summary-bar {{ display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }}
  .stat-card {{
    background: #1a1a2e; border: 1px solid #2a2a44;
    border-radius: 6px; padding: 12px 16px; min-width: 120px;
  }}
  .stat-card .num {{ font-size: 24px; font-weight: 700; color: #f0b932; }}
  .stat-card .lbl {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.4px; margin-top: 2px; }}
  .role-icon {{ width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 5px; flex-shrink: 0; }}
  .empty-state {{ color: #555; padding: 40px; text-align: center; font-size: 15px; }}
</style>
</head>
<body>

<header>
  <h1>&#9876; WoW BiS Competition Tracker</h1>
  <span class="updated">
    <span>Last scraped: {generated_at}</span>
    <span class="spec-count" style="color:{specs_color};border-color:{specs_color};background:{specs_color}18">{specs_label}</span>
  </span>
</header>

<div class="controls">
  <div class="role-filters">
    <label>Role:</label>
    <button class="role-btn active" data-role="All">All</button>
    <button class="role-btn" data-role="Tank">Tank</button>
    <button class="role-btn" data-role="Healer">Healer</button>
    <button class="role-btn" data-role="DPS">DPS</button>
  </div>
  <div class="spec-select-wrap">
    <label for="specSelect">Spec:</label>
    <select id="specSelect">
      <option value="">— Select a spec —</option>
    </select>
  </div>
</div>

<div class="tab-bar">
  <div class="tab active" data-tab="my-spec">My Spec BiS</div>
  <div class="tab" data-tab="contested">Most Contested Items</div>
</div>

<div id="my-spec" class="view active">
  <div id="spec-content"><p class="empty-state">Select a spec above to see their BiS list.</p></div>
</div>

<div id="contested" class="view">
  <div id="contested-content"></div>
</div>

<script>
const BIS_DATA = {data_json};
const CLASS_COLORS = {colors_json};

let activeRole = 'All';

function getColor(cls) {{ return CLASS_COLORS[cls] || '#888'; }}

const ROLE_ICONS = {{
  Tank: `<svg class="role-icon" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" title="Tank">
    <path d="M10 1 L18 4.5 V10.5 C18 15 14.5 18.2 10 19.5 C5.5 18.2 2 15 2 10.5 V4.5 Z" fill="#1a4a7a" stroke="#4a90d9" stroke-width="1.2"/>
    <path d="M10 4 L15.5 6.5 V10.5 C15.5 13.5 13 15.8 10 17 C7 15.8 4.5 13.5 4.5 10.5 V6.5 Z" fill="#2a6aaa" stroke="#6ab0ff" stroke-width="0.8"/>
    <path d="M10 7 L12.5 11 L10 13 L7.5 11 Z" fill="#aad4ff" opacity="0.9"/>
  </svg>`,
  Healer: `<svg class="role-icon" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" title="Healer">
    <circle cx="10" cy="10" r="9" fill="#1a3a1a" stroke="#4caf50" stroke-width="1.2"/>
    <circle cx="10" cy="10" r="7" fill="#2a5a2a" stroke="#6acc6a" stroke-width="0.6"/>
    <rect x="8.5" y="4.5" width="3" height="11" rx="1" fill="#aaffaa"/>
    <rect x="4.5" y="8.5" width="11" height="3" rx="1" fill="#aaffaa"/>
  </svg>`,
  DPS: `<svg class="role-icon" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" title="DPS">
    <line x1="4" y1="16" x2="14" y2="3" stroke="#e05252" stroke-width="2.2" stroke-linecap="round"/>
    <polygon points="14,3 17,5 15,7" fill="#e05252"/>
    <rect x="2.5" y="15" width="3" height="2" rx="0.5" fill="#c03030" transform="rotate(-45 4 16)"/>
    <line x1="16" y1="16" x2="6" y2="3" stroke="#ff8888" stroke-width="2.2" stroke-linecap="round" opacity="0.7"/>
    <polygon points="6,3 3,5 5,7" fill="#ff8888" opacity="0.7"/>
    <rect x="14.5" y="15" width="3" height="2" rx="0.5" fill="#c03030" opacity="0.7" transform="rotate(45 16 16)"/>
  </svg>`,
}};

function badge(cls, spec, role) {{
  const color = getColor(cls);
  return `<span class="badge" style="color:${{color}};background:${{color}}1a">${{ROLE_ICONS[role] || ''}}<span>${{spec}} ${{cls}}</span></span>`;
}}

function filteredSpecs() {{
  return activeRole === 'All' ? BIS_DATA : BIS_DATA.filter(s => s.role === activeRole);
}}

// Build spec dropdown based on active role filter
function populateDropdown() {{
  const select = document.getElementById('specSelect');
  const current = select.value;
  select.innerHTML = '<option value="">— Select a spec —</option>';

  const specs = filteredSpecs();
  // Group by role for optgroups
  const roles = ['Tank', 'Healer', 'DPS'];
  const grouped = {{}};
  roles.forEach(r => grouped[r] = []);
  specs.forEach((s, _) => {{
    const role = s.role || 'DPS';
    if (grouped[role]) grouped[role].push(s);
  }});

  roles.forEach(role => {{
    if (!grouped[role].length) return;
    const grp = document.createElement('optgroup');
    grp.label = role;
    grouped[role].forEach(s => {{
      const idx = BIS_DATA.indexOf(s);
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `${{s.spec}} ${{s.class}}`;
      if (String(idx) === current) opt.selected = true;
      grp.appendChild(opt);
    }});
    select.appendChild(grp);
  }});

  // If previously selected spec is now hidden by filter, clear the spec view
  if (current && !select.querySelector(`option[value="${{current}}"]`)) {{
    document.getElementById('spec-content').innerHTML =
      '<p class="empty-state">Select a spec above to see their BiS list.</p>';
  }}
}}

function renderSpecView(specIdx) {{
  const spec = BIS_DATA[specIdx];
  if (!spec) return;
  const color = getColor(spec.class);
  const contested = spec.bis_items.filter(i => i.competitors.length > 0).length;
  const exclusive = spec.bis_items.length - contested;

  let html = `
    <div class="summary-bar">
      <div class="stat-card">
        <div class="num" style="color:${{color}}">${{spec.bis_items.length}}</div>
        <div class="lbl">BiS Items</div>
      </div>
      <div class="stat-card">
        <div class="num" style="color:#ff6b6b">${{contested}}</div>
        <div class="lbl">Contested</div>
      </div>
      <div class="stat-card">
        <div class="num" style="color:#3fc7eb">${{exclusive}}</div>
        <div class="lbl">Uncontested</div>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th class="col-slot">Slot</th>
          <th>Item</th>
          <th class="col-source">Source</th>
          <th class="col-comp">Also BiS for</th>
        </tr>
      </thead>
      <tbody>`;

  spec.bis_items.forEach(item => {{
    // Filter competitors by active role
    const visibleComp = activeRole === 'All'
      ? item.competitors
      : item.competitors.filter(c => c.role === activeRole);

    const compHtml = visibleComp.length
      ? visibleComp.map(c => badge(c.class, c.spec, c.role)).join('')
      : (item.competitors.length
          ? `<span class="no-comp">None in this role filter</span>`
          : `<span class="no-comp">Uncontested</span>`);

    const rowClass = item.competitors.length >= 2 ? 'row-hot' : item.competitors.length === 1 ? 'row-warm' : '';
    const linkClass = item.competitors.length > 0 ? 'contested' : '';
    const url = item.wowhead_url || `https://www.wowhead.com/search?q=${{encodeURIComponent(item.item_name)}}`;

    html += `
      <tr class="${{rowClass}}">
        <td class="col-slot">${{item.slot}}</td>
        <td class="item-name"><a href="${{url}}" target="_blank" class="${{linkClass}}">${{item.item_name}}</a></td>
        <td class="col-source">${{item.source}}</td>
        <td class="col-comp">${{compHtml}}</td>
      </tr>`;
  }});

  html += `</tbody></table>`;
  document.getElementById('spec-content').innerHTML = html;
  attachResizers();
}}

function renderContestedView() {{
  const specs = filteredSpecs();

  // Rebuild competition map from filtered specs only
  const itemMap = {{}};
  specs.forEach(spec => {{
    spec.bis_items.forEach(item => {{
      if (!item.item_id) return;
      if (!itemMap[item.item_id]) {{
        itemMap[item.item_id] = {{
          item_id: item.item_id,
          item_name: item.item_name,
          wowhead_url: item.wowhead_url,
          specs: [],
        }};
      }}
      itemMap[item.item_id].specs.push({{
        class: spec.class,
        spec: spec.spec,
        role: spec.role || 'DPS',
        slot: item.slot,
        source: item.source,
      }});
    }});
  }});

  const contested = Object.values(itemMap)
    .filter(i => i.specs.length > 1)
    .sort((a, b) => b.specs.length - a.specs.length);

  const total = Object.values(itemMap).length;

  let html = `
    <div class="summary-bar">
      <div class="stat-card"><div class="num">${{total}}</div><div class="lbl">Unique Items</div></div>
      <div class="stat-card"><div class="num" style="color:#ff6b6b">${{contested.length}}</div><div class="lbl">Contested</div></div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Item</th>
          <th class="col-count">Specs</th>
          <th>Wanted By</th>
        </tr>
      </thead>
      <tbody>`;

  contested.forEach(item => {{
    const countClass = item.specs.length >= 3 ? 'hot' : 'warm';
    const badges = item.specs.map(s => badge(s.class, s.spec, s.role)).join('');
    html += `
      <tr>
        <td class="item-name"><a href="${{item.wowhead_url}}" target="_blank">${{item.item_name}}</a></td>
        <td class="col-count"><span class="contest-count ${{countClass}}">${{item.specs.length}}</span></td>
        <td>${{badges}}</td>
      </tr>`;
  }});

  if (!contested.length) {{
    html += `<tr><td colspan="3" class="empty-state">No contested items in this filter.</td></tr>`;
  }}

  html += `</tbody></table>`;
  document.getElementById('contested-content').innerHTML = html;
  attachResizers();
}}

// Role filter buttons
document.querySelectorAll('.role-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeRole = btn.dataset.role;
    populateDropdown();
    renderContestedView();
    // Re-render spec view if one is selected
    const idx = document.getElementById('specSelect').value;
    if (idx !== '') renderSpecView(parseInt(idx));
  }});
}});

// Spec select
document.getElementById('specSelect').addEventListener('change', function() {{
  if (this.value !== '') renderSpecView(parseInt(this.value));
  else document.getElementById('spec-content').innerHTML =
    '<p class="empty-state">Select a spec above to see their BiS list.</p>';
}});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  }});
}});

function makeResizable(table) {{
  table.querySelectorAll('th').forEach(th => {{
    const resizer = document.createElement('div');
    resizer.className = 'col-resizer';
    th.appendChild(resizer);
    // Set explicit initial width so resizing works with table-layout:fixed
    th.style.width = th.offsetWidth + 'px';

    let startX, startW;
    resizer.addEventListener('mousedown', e => {{
      startX = e.pageX;
      startW = th.offsetWidth;
      resizer.classList.add('dragging');
      const onMove = e => {{ th.style.width = Math.max(60, startW + e.pageX - startX) + 'px'; }};
      const onUp   = () => {{
        resizer.classList.remove('dragging');
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }};
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
      e.preventDefault();
    }});
  }});
}}

// Re-attach resizers whenever a view is re-rendered
function attachResizers() {{
  document.querySelectorAll('table').forEach(makeResizable);
}}

// Init
populateDropdown();
renderContestedView();
attachResizers();
</script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("index.html written.")
