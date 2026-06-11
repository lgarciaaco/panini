"""Print extras available for trading."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from src import catalog, inventory, reports


def main():
    inventory.init(catalog.all_codes())
    extras = inventory.all_extras()
    from rich.console import Console
    c = Console()
    if not extras:
        c.print("[dim]No extras yet. Extras are added when scanning loose sticker photos.[/dim]")
        return
    total_cards = sum(e["qty"] for e in extras)
    c.print(f"\n[bold yellow]Extras available for trading[/bold yellow]  ({len(extras)} types, {total_cards} cards)\n")
    reports.print_extras_list(extras, catalog)


if __name__ == "__main__":
    main()
