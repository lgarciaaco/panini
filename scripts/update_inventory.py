"""
DB update tool called by the Cursor agent after it analyzes each image.

Usage — album page:
  python3.11 scripts/update_inventory.py \\
    --image IMG_0410.jpeg \\
    --type album_page \\
    --team SUI \\
    --owned SUI2,SUI6

Usage — loose extras:
  python3.11 scripts/update_inventory.py \\
    --image IMG_0400.jpeg \\
    --type extras \\
    --stickers ARG3,COL13,URU2,BRA7

The agent always validates codes against the catalog before calling this.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import click
from rich.console import Console
from src import catalog, inventory

console = Console()


@click.command()
@click.option("--image", required=True, help="Source image filename (for audit log)")
@click.option("--type", "img_type", required=True,
              type=click.Choice(["album_page", "extras"]),
              help="Image type")
@click.option("--team", default=None, help="Team code for album_page scans (e.g. SUI)")
@click.option("--owned", default="",
              help="Comma-separated codes of FILLED slots (album_page)")
@click.option("--stickers", default="",
              help="Comma-separated codes seen in extras pile")
@click.option("--move/--no-move", default=True,
              help="Move image to images/processed/ when done")
def main(image, img_type, team, owned, stickers, move):
    all_codes = catalog.all_codes()
    inventory.init(all_codes)

    owned_list = [c.strip().upper().replace(" ", "") for c in owned.split(",") if c.strip()]
    sticker_list = [c.strip().upper().replace(" ", "") for c in stickers.split(",") if c.strip()]

    # Validate all codes
    bad = [c for c in owned_list + sticker_list if c not in all_codes]
    if bad:
        console.print(f"[red]Unknown sticker codes (check catalog): {bad}[/red]")
        sys.exit(1)

    if img_type == "album_page":
        if not team:
            console.print("[red]--team is required for album_page[/red]")
            sys.exit(1)
        team = team.upper()
        all_team_codes = [s["code"] for s in catalog.by_team(team)]

        # Mark owned
        for code in owned_list:
            inventory.upsert_owned(code, image)

        # Mark the rest of the team as missing (only if not already owned)
        inventory.mark_team_missing(team, all_team_codes)
        inventory.log_scan(image, img_type, team, len(owned_list) + len(all_team_codes), "")

        console.print(
            f"[green]✓[/green] {image} → {team} "
            f"[green]{len(owned_list)} owned[/green], "
            f"{len(all_team_codes) - len(owned_list)} missing"
        )

    elif img_type == "extras":
        for code in sticker_list:
            inventory.upsert_extra(code, image)
        inventory.log_scan(image, img_type, None, len(sticker_list), "")
        console.print(
            f"[yellow]✓[/yellow] {image} → extras "
            f"[yellow]{len(sticker_list)} stickers[/yellow] added"
        )

    # Move image to processed/
    if move:
        import shutil
        from pathlib import Path
        inbox_paths = [
            os.path.join(os.path.dirname(__file__), "..", "images", "inbox", image),
            os.path.join(os.path.dirname(__file__), "..", "images", "processed", image),
        ]
        processed_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "images", "processed")
        )
        for src in inbox_paths:
            src = os.path.normpath(src)
            if os.path.exists(src) and "inbox" in src:
                os.makedirs(processed_dir, exist_ok=True)
                shutil.move(src, os.path.join(processed_dir, image))
                break


if __name__ == "__main__":
    main()
