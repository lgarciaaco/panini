# Panini FIFA World Cup 2026 — Collection Tracker

Fully agentic sticker collection tracker. Drop photos, talk to the Cursor agent — you never run a single command.

## How it works

1. **Drop photos** into `images/inbox/` (album pages or loose sticker piles)
2. **Tell the Cursor agent** "scan my inbox"
3. **Done.** The agent scans every image, updates the database, generates the report, and publishes it live.

No manual commands. No terminal. No git. The agent handles the entire pipeline: image analysis, inventory updates, report generation, commit, and push to GitHub Pages.

## Live report

**https://lgarciaaco.github.io/panini/**

Auto-refreshes every 5 minutes in the browser. Updated automatically by the agent after every scan.

- Dark mode, mobile-first layout
- Tabs: Missing | Owned | Extras
- Collapsible groups and teams
- Instant search by player name, team, or code
- Family face avatars in the header (drop photos in `images/faces/`)

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
├── docs/
│   └── index.html         # GitHub Pages source (auto-generated)
├── images/
│   ├── inbox/             # Drop new photos here
│   ├── processed/         # Moved here after scan
│   ├── faces/             # Family member photos for report header
│   └── extras/            # Optional: dedicated extras folder
├── reports/               # Generated HTML reports (local archive)
├── src/
│   ├── catalog.py         # Catalog loader/queries
│   ├── inventory.py       # Database operations
│   └── reports.py         # Terminal output (Rich)
└── scripts/
    ├── build_catalog.py   # Generate catalog.json (one-time)
    ├── scan.py            # List inbox contents
    ├── update_inventory.py# Update DB from scan results
    ├── status.py          # Collection overview
    ├── missing.py         # Missing sticker list
    ├── trade.py           # Extras / trade list
    ├── report.py          # HTML report generator
    └── publish.py         # Regenerate report + commit + push
```

## Album facts

- **980 total stickers** — the largest Panini World Cup album ever
- **48 teams × 20 stickers** each
  - #1 = Team badge (foil ★)
  - #2–12, #14–20 = Players
  - #13 = Team photo
- **FWC 1–19** = Intro + FIFA Museum foils
- Teams organized by 12 groups (A–L), 4 teams per group
