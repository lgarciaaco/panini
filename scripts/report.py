"""Generate a self-contained mobile-friendly HTML report."""
import os, sys, json, base64, glob
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

import click
from src import catalog, inventory

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
FACES_DIR = os.path.join(os.path.dirname(__file__), "..", "images", "faces")


def load_faces() -> list[str]:
    """Return base64 data URIs for all images in images/faces/."""
    uris = []
    if not os.path.isdir(FACES_DIR):
        return uris
    for path in sorted(glob.glob(os.path.join(FACES_DIR, "*"))):
        ext = os.path.splitext(path)[1].lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "webp": "image/webp", "gif": "image/gif"}.get(ext.lstrip("."))
        if not mime:
            continue
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        uris.append(f"data:{mime};base64,{b64}")
    return uris


def build_html(cat_stickers, inv_stats, inv_owned, inv_missing, inv_extras, grp_data, faces=None) -> str:
    now = datetime.now().strftime("%b %d, %Y %H:%M")
    total = len(cat_stickers)
    owned_n = inv_stats.get("owned", 0)
    missing_n = inv_stats.get("missing", 0)
    extra_n = inv_stats.get("extra", 0)
    extra_qty = inv_stats.get("extra_qty", 0)
    pct = round(owned_n / total * 100, 1) if total else 0
    faces = faces or []

    faces_html = ""
    if faces:
        avatars = "".join(f'<img class="face-avatar" src="{uri}" alt="collector"/>' for uri in faces)
        faces_html = f'<div class="faces-row">{avatars}</div>'

    # Build per-sticker lookup
    sticker_map = {s["code"]: s for s in cat_stickers}

    # Build missing list HTML by group/team
    missing_set = set(inv_missing)
    owned_set = set(inv_owned)
    extras_map = {e["code"]: e["qty"] for e in inv_extras}

    # Build group sections for missing + owned tabs
    missing_html = ""
    owned_html = ""
    extras_html = ""

    for grp in sorted(grp_data.keys()):
        teams = grp_data[grp]
        missing_html += f'<div class="group-block"><div class="group-label">Group {grp}</div>'
        owned_html   += f'<div class="group-block"><div class="group-label">Group {grp}</div>'
        for tc in teams:
            meta = catalog.team_meta(tc)
            prog = inventory.team_progress(tc)
            have = prog["have"]
            ttl = meta["total"]
            pct_t = round(have / ttl * 100) if ttl else 0
            team_missing = [c for c in [f"{tc}{n}" for n in range(1, ttl + 1)] if c in missing_set]
            team_owned   = [c for c in [f"{tc}{n}" for n in range(1, ttl + 1)] if c in owned_set]

            if not team_missing:
                badge = '<span class="complete-badge">✓ Complete</span>'
            else:
                badge = f'<span class="missing-count">{len(team_missing)} missing</span>'

            owned_badge = f'<span class="complete-badge">{len(team_owned)} owned</span>' if team_owned else '<span class="missing-count">0 owned</span>'

            missing_rows = ""
            for code in team_missing:
                s = sticker_map.get(code, {})
                player = s.get("player") or s.get("description", code)
                foil = '<span class="foil-badge">★ foil</span>' if s.get("foil") else ""
                missing_rows += f'<div class="sticker-row"><span class="s-code">{s.get("display", code)}</span><span class="s-name">{player}{foil}</span></div>'

            owned_rows = ""
            for code in team_owned:
                s = sticker_map.get(code, {})
                player = s.get("player") or s.get("description", code)
                foil = '<span class="foil-badge">★ foil</span>' if s.get("foil") else ""
                owned_rows += f'<div class="sticker-row owned-row"><span class="s-code">{s.get("display", code)}</span><span class="s-name">{player}{foil}</span></div>'

            team_block_missing = f'''
<div class="team-block">
  <div class="team-header" onclick="toggleTeam(this)">
    <span class="team-flag">{meta.get("flag","")}</span>
    <span class="team-name">{meta.get("team_name", tc)}</span>
    <span class="team-progress-text">{have}/{ttl}</span>
    <div class="team-bar-wrap"><div class="team-bar" style="width:{pct_t}%"></div></div>
    {badge}
    <span class="chevron">›</span>
  </div>
  <div class="team-stickers collapsed">{missing_rows if missing_rows else '<div class="all-good">All stickers collected!</div>'}</div>
</div>'''

            team_block_owned = f'''
<div class="team-block">
  <div class="team-header" onclick="toggleTeam(this)">
    <span class="team-flag">{meta.get("flag","")}</span>
    <span class="team-name">{meta.get("team_name", tc)}</span>
    <span class="team-progress-text">{have}/{ttl}</span>
    <div class="team-bar-wrap"><div class="team-bar" style="width:{pct_t}%"></div></div>
    {owned_badge}
    <span class="chevron">›</span>
  </div>
  <div class="team-stickers collapsed">{owned_rows if owned_rows else '<div class="all-good" style="color:var(--muted)">None yet</div>'}</div>
</div>'''

            missing_html += team_block_missing
            owned_html   += team_block_owned
        missing_html += "</div>"
        owned_html   += "</div>"

    # Build extras tab
    if inv_extras:
        extras_html = '<div class="extras-grid">'
        for item in sorted(inv_extras, key=lambda x: x["code"]):
            s = sticker_map.get(item["code"], {})
            player = s.get("player") or s.get("description", item["code"])
            foil = '<span class="foil-badge">★</span>' if s.get("foil") else ""
            qty = item["qty"]
            qty_label = f'<span class="extra-qty">×{qty}</span>' if qty > 1 else '<span class="extra-qty">×1</span>'
            extras_html += f'''<div class="extra-card">
  <div class="extra-code">{s.get("display", item["code"])}</div>
  <div class="extra-team">{s.get("flag","")} {s.get("team_name","")}</div>
  <div class="extra-player">{player}{foil}</div>
  {qty_label}
</div>'''
        extras_html += "</div>"
    else:
        extras_html = '<p class="empty-state">No extras scanned yet.<br>Drop photos of your duplicate stickers in <code>images/inbox/</code> and run scan.py</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta http-equiv="refresh" content="300">
<title>⚽ WC 2026 Collection</title>
<style>
  :root {{
    --bg: #0a0e1a;
    --surface: #131929;
    --surface2: #1c2438;
    --accent: #00c9ff;
    --green: #22c55e;
    --yellow: #fbbf24;
    --red: #f87171;
    --text: #e2e8f0;
    --muted: #64748b;
    --foil: #ffd700;
    --radius: 12px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}

  /* Header */
  .header {{
    background: linear-gradient(135deg, #0f2044 0%, #1a3a6e 100%);
    padding: 20px 16px 16px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 20px rgba(0,0,0,0.5);
  }}
  .header-title {{
    font-size: 22px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }}
  .header-title span {{ color: var(--accent); }}
  .pct-label {{
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 4px;
  }}
  .main-bar-bg {{
    height: 8px;
    background: rgba(255,255,255,0.1);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 10px;
  }}
  .main-bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--green));
    border-radius: 4px;
    transition: width 0.8s ease;
  }}
  .stats-row {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .stat-chip {{
    background: rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 4px 10px;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .stat-chip .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
  .dot-green {{ background: var(--green); }}
  .dot-red {{ background: var(--red); }}
  .dot-yellow {{ background: var(--yellow); }}

  /* Family faces */
  .faces-row {{
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 12px;
  }}
  .face-avatar {{
    width: 52px;
    height: 52px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--accent);
    box-shadow: 0 2px 10px rgba(0,201,255,0.3);
  }}

  /* Search */
  .search-wrap {{
    padding: 10px 16px 0;
    position: sticky;
    top: 145px;
    z-index: 99;
    background: var(--bg);
  }}
  .search-box {{
    width: 100%;
    padding: 10px 14px;
    background: var(--surface2);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: var(--radius);
    color: var(--text);
    font-size: 15px;
    outline: none;
  }}
  .search-box::placeholder {{ color: var(--muted); }}
  .search-box:focus {{ border-color: var(--accent); }}

  /* Tabs */
  .tabs {{
    display: flex;
    padding: 10px 16px 0;
    gap: 4px;
    position: sticky;
    top: 200px;
    background: var(--bg);
    z-index: 98;
  }}
  .tab {{
    flex: 1;
    text-align: center;
    padding: 9px 4px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    color: var(--muted);
    background: none;
    border: none;
    transition: all 0.2s;
  }}
  .tab.active {{
    background: var(--surface2);
    color: var(--accent);
  }}

  /* Content */
  .content {{ padding: 10px 16px 40px; }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}

  /* Group block */
  .group-block {{ margin-bottom: 8px; }}
  .group-label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent);
    padding: 10px 4px 4px;
  }}

  /* Team block */
  .team-block {{
    background: var(--surface);
    border-radius: var(--radius);
    margin-bottom: 6px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
  }}
  .team-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 14px;
    cursor: pointer;
    user-select: none;
  }}
  .team-header:active {{ background: var(--surface2); }}
  .team-flag {{ font-size: 20px; flex-shrink: 0; }}
  .team-name {{ flex: 1; font-size: 15px; font-weight: 600; min-width: 0; }}
  .team-progress-text {{ font-size: 12px; color: var(--muted); flex-shrink: 0; }}
  .team-bar-wrap {{ width: 48px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; flex-shrink: 0; }}
  .team-bar {{ height: 100%; background: var(--green); border-radius: 2px; }}
  .missing-count {{ font-size: 12px; color: var(--red); flex-shrink: 0; }}
  .complete-badge {{ font-size: 12px; color: var(--green); flex-shrink: 0; }}
  .chevron {{
    color: var(--muted);
    font-size: 18px;
    transition: transform 0.2s;
    flex-shrink: 0;
  }}
  .team-header.open .chevron {{ transform: rotate(90deg); }}

  /* Sticker rows */
  .team-stickers {{ background: var(--surface2); }}
  .team-stickers.collapsed {{ display: none; }}
  .sticker-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    border-top: 1px solid rgba(255,255,255,0.04);
    font-size: 14px;
  }}
  .s-code {{ color: var(--accent); font-weight: 600; width: 54px; flex-shrink: 0; font-size: 13px; }}
  .s-name {{ flex: 1; color: var(--text); }}
  .foil-badge {{
    background: linear-gradient(90deg, #ffd700, #ffaa00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 11px;
    font-weight: 700;
    margin-left: 4px;
  }}
  .all-good {{ padding: 10px 14px; color: var(--green); font-size: 13px; }}
  .owned-row .s-code {{ color: var(--green); }}
  .owned-row {{ opacity: 0.9; }}

  /* Extras grid */
  .extras-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 8px;
    padding-top: 8px;
  }}
  .extra-card {{
    background: var(--surface);
    border-radius: var(--radius);
    padding: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    position: relative;
  }}
  .extra-code {{ font-size: 16px; font-weight: 700; color: var(--accent); }}
  .extra-team {{ font-size: 12px; color: var(--muted); margin: 2px 0; }}
  .extra-player {{ font-size: 13px; color: var(--text); }}
  .extra-qty {{
    position: absolute;
    top: 10px;
    right: 10px;
    background: var(--yellow);
    color: #000;
    font-size: 11px;
    font-weight: 700;
    border-radius: 10px;
    padding: 2px 6px;
  }}

  /* Empty state */
  .empty-state {{
    text-align: center;
    color: var(--muted);
    padding: 40px 20px;
    font-size: 15px;
    line-height: 1.6;
  }}
  .empty-state code {{
    background: var(--surface2);
    padding: 2px 6px;
    border-radius: 4px;
    color: var(--accent);
  }}

  /* Footer */
  .footer {{
    text-align: center;
    color: var(--muted);
    font-size: 11px;
    padding: 20px;
    border-top: 1px solid rgba(255,255,255,0.05);
  }}

  /* Search highlight */
  .hidden {{ display: none !important; }}

  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #f1f5f9;
      --surface: #ffffff;
      --surface2: #f8fafc;
      --text: #1e293b;
      --muted: #94a3b8;
    }}
    .header {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; }}
    .search-wrap {{ background: var(--bg); }}
    .tabs {{ background: var(--bg); }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-title">⚽ <span>WC 2026</span> Collection</div>
  {faces_html}
  <div class="pct-label">{owned_n} / {total} stickers &nbsp;·&nbsp; {pct}% complete</div>
  <div class="main-bar-bg">
    <div class="main-bar-fill" style="width:{pct}%"></div>
  </div>
  <div class="stats-row">
    <div class="stat-chip"><div class="dot dot-green"></div>{owned_n} owned</div>
    <div class="stat-chip"><div class="dot dot-red"></div>{missing_n} missing</div>
    <div class="stat-chip"><div class="dot dot-yellow"></div>{extra_qty} extras ({extra_n} types)</div>
  </div>
</div>

<div class="search-wrap">
  <input class="search-box" type="search" placeholder="Search player, team, code…" oninput="doSearch(this.value)" />
</div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('missing', this)">Missing ({missing_n})</button>
  <button class="tab" onclick="switchTab('owned', this)">Owned ({owned_n})</button>
  <button class="tab" onclick="switchTab('extras', this)">Extras ({extra_qty})</button>
</div>

<div class="content">
  <div id="tab-missing" class="tab-panel active">
    {missing_html}
  </div>
  <div id="tab-owned" class="tab-panel">
    {owned_html}
  </div>
  <div id="tab-extras" class="tab-panel">
    {extras_html}
  </div>
</div>

<div class="footer">Generated {now} &nbsp;·&nbsp; Panini FIFA World Cup 2026 Tracker</div>

<script>
function switchTab(name, btn) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}}

function toggleTeam(header) {{
  const stickers = header.nextElementSibling;
  const isOpen = !stickers.classList.contains('collapsed');
  stickers.classList.toggle('collapsed', isOpen);
  header.classList.toggle('open', !isOpen);
}}

function doSearch(q) {{
  q = q.toLowerCase().trim();
  if (!q) {{
    document.querySelectorAll('.team-block, .extra-card, .sticker-row').forEach(el => el.classList.remove('hidden'));
    document.querySelectorAll('.team-stickers').forEach(el => el.classList.add('collapsed'));
    document.querySelectorAll('.team-header').forEach(el => el.classList.remove('open'));
    return;
  }}
  document.querySelectorAll('.tab-panel').forEach(panel => {{
    panel.querySelectorAll('.team-block').forEach(block => {{
      const rows = block.querySelectorAll('.sticker-row');
      let anyMatch = false;
      rows.forEach(row => {{
        const txt = row.textContent.toLowerCase();
        const match = txt.includes(q);
        row.classList.toggle('hidden', !match);
        if (match) anyMatch = true;
      }});
      const teamTxt = block.querySelector('.team-name')?.textContent.toLowerCase() || '';
      if (teamTxt.includes(q)) {{
        rows.forEach(r => r.classList.remove('hidden'));
        anyMatch = true;
      }}
      block.classList.toggle('hidden', !anyMatch);
      if (anyMatch) {{
        block.querySelector('.team-stickers')?.classList.remove('collapsed');
        block.querySelector('.team-header')?.classList.add('open');
      }}
    }});
  }});
  document.querySelectorAll('.extra-card').forEach(card => {{
    card.classList.toggle('hidden', !card.textContent.toLowerCase().includes(q));
  }});
}}
</script>
</body>
</html>"""


@click.command()
@click.option("--out", default=None, help="Output file path (default: reports/wc2026_YYYY-MM-DD.html)")
def main(out):
    all_codes = catalog.all_codes()
    inventory.init(all_codes)

    if not out:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        out = os.path.join(REPORTS_DIR, f"wc2026_{date_str}.html")
    out = os.path.normpath(out)

    stats = inventory.stats()
    missing = inventory.all_missing()
    extras = inventory.all_extras()
    owned = inventory.owned_codes()
    grps = catalog.groups()
    cat_stickers = catalog.load()

    faces = load_faces()
    html = build_html(cat_stickers, stats, owned, missing, extras, grps, faces=faces)

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    docs_index = os.path.join(docs_dir, "index.html")
    with open(docs_index, "w", encoding="utf-8") as f:
        f.write(html)

    from rich.console import Console
    c = Console()
    c.print(f"\n[green]✓[/green] Report saved: [bold]{out}[/bold]")
    c.print(f"[green]✓[/green] GitHub Pages: [bold]{os.path.normpath(docs_index)}[/bold]")
    c.print(f"  Open in Safari or AirDrop to iPhone\n")


if __name__ == "__main__":
    main()
