"""
Scan workflow — lists what needs processing and prints agent instructions.
The actual image analysis is done by the Cursor agent (it reads the images).

Run this to see what's in the inbox, then say "scan my inbox" in Cursor chat.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
INBOX = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "images", "inbox"))
SUPPORTED = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def main():
    images = sorted([p for p in Path(INBOX).iterdir() if p.suffix.lower() in SUPPORTED])

    if not images:
        console.print(f"[yellow]No images found in images/inbox/[/yellow]")
        console.print("Drop photos there, then say [cyan]'scan my inbox'[/cyan] in Cursor chat.")
        return

    console.print(f"\n[bold cyan]Panini WC 2026 — Inbox[/bold cyan]")
    console.print(f"  {len(images)} image(s) ready to scan\n")

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#", width=4)
    table.add_column("File", style="dim")
    table.add_column("Size")
    for i, p in enumerate(images, 1):
        size = f"{p.stat().st_size // 1024}KB"
        table.add_row(str(i), p.name, size)
    console.print(table)

    console.print("\n[bold]Next step:[/bold]")
    console.print("  In Cursor chat, say: [cyan bold]scan my inbox[/cyan bold]")
    console.print("  The agent will read each image and update your inventory.\n")


if __name__ == "__main__":
    main()
