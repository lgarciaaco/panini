# Panini FIFA World Cup 2026 — Collection Tracker

Agentic system to track your Panini sticker collection via photos.

## Quick start

No external API key needed — vision analysis runs through Cursor's built-in AI.

```bash
# 1. Install dependencies
/Library/Frameworks/Python.framework/Versions/3.11/bin/pip3 install -r requirements.txt

# 2. Build the sticker catalog (one-time)
python3.11 scripts/build_catalog.py

# 3. Drop photos in images/inbox/

# 4. List what's ready to scan
python3.11 scripts/scan.py

# 5. In Cursor chat: say "scan my inbox"
#    The agent reads each image and updates the DB automatically.

# 6. View results
python3.11 scripts/status.py      # terminal overview
python3.11 scripts/missing.py     # missing stickers grouped by team
python3.11 scripts/trade.py       # extras available for trading
python3.11 scripts/report.py      # generate HTML report → open on iPhone
```

## Photo guide

| What to photograph | Result |
|---|---|
| Open album spread (any page) | Reads owned + missing slots for that team |
| Pile of loose duplicate cards | Adds all visible cards as extras for trading |

**Tips:**
- Shoot album pages flat with good lighting, avoid glare
- For extras pile: spread cards face-up so codes are readable

## Project structure

```
panini/
├── data/
│   ├── catalog.json       # 980-sticker master list
│   └── inventory.db       # SQLite database (auto-created)
├── images/
│   ├── inbox/             # Drop new photos here
│   ├── processed/         # Moved here after scan
│   └── extras/            # Optional: dedicated extras folder
├── reports/               # Generated HTML reports
├── src/
│   ├── catalog.py         # Catalog loader/queries
│   ├── inventory.py       # Database operations
│   ├── vision.py          # Claude vision integration
│   └── reports.py         # Terminal output (Rich)
└── scripts/
    ├── build_catalog.py   # Generate catalog.json (one-time)
    ├── scan.py            # Main scan pipeline
    ├── status.py          # Collection overview
    ├── missing.py         # Missing sticker list
    ├── trade.py           # Extras / trade list
    └── report.py          # HTML report generator
```

## Live report

**https://lgarciaaco.github.io/panini/**

Auto-refreshes every 5 minutes. Run `python3.11 scripts/report.py` to update — it writes both `reports/wc2026_YYYY-MM-DD.html` and `docs/index.html` (GitHub Pages source).

- Dark mode, mobile-first layout
- Tabs: Missing | Owned | Extras
- Collapsible groups and teams
- Instant search by player name, team, or code
- Family face avatars in the header (drop photos in `images/faces/`)

## Album facts

- **980 total stickers** — the largest Panini World Cup album ever
- **48 teams × 20 stickers** each
  - #1 = Team badge (foil ★)
  - #2–12, #14–20 = Players
  - #13 = Team photo
- **FWC 1–19** = Intro + FIFA Museum foils
- Teams organized by 12 groups (A–L), 4 teams per group
