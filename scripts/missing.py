"""Print all missing stickers grouped by team."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

import click
from src import catalog, inventory, reports


@click.command()
@click.option("--team", default=None, help="Filter to a specific team code (e.g. ARG, FWC)")
@click.option("--group", default=None, help="Filter to a specific group (e.g. A, B)")
def main(team, group):
    inventory.init(catalog.all_codes())
    missing = inventory.all_missing()

    if team:
        team = team.upper()
        missing = [c for c in missing if c.startswith(team)]
    elif group:
        group = group.upper()
        grp_teams = catalog.groups().get(group, [])
        missing = [c for c in missing if any(c.startswith(tc) for tc in grp_teams)]

    if not missing:
        from rich.console import Console
        Console().print("[green]No missing stickers in this filter![/green]")
        return

    reports.print_missing_list(missing, catalog)

if __name__ == "__main__":
    main()
