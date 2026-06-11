"""Rich terminal output helpers."""
from rich.console import Console
from rich.table import Table
from rich.progress import BarColumn, Progress, TextColumn
from rich import box
from rich.text import Text

console = Console()


def print_stats(stats: dict, catalog_total: int) -> None:
    owned = stats.get("owned", 0)
    missing = stats.get("missing", 0)
    extra = stats.get("extra", 0)
    extra_qty = stats.get("extra_qty", 0)

    pct = int(owned / catalog_total * 100) if catalog_total else 0
    bar_filled = pct // 2
    bar_empty = 50 - bar_filled
    bar = f"[green]{'█' * bar_filled}[/green][dim]{'░' * bar_empty}[/dim]"

    console.print()
    console.print(f"[bold cyan]⚽ Panini FIFA World Cup 2026[/bold cyan]")
    console.print(f"  {bar} [bold]{pct}%[/bold] ({owned}/{catalog_total})")
    console.print(f"  [green]Owned in album :[/green] [bold]{owned}[/bold]")
    console.print(f"  [red]Missing        :[/red] [bold]{missing}[/bold]")
    console.print(f"  [yellow]Extras (trade) :[/yellow] [bold]{extra}[/bold] sticker types, [bold]{extra_qty}[/bold] total cards")
    console.print()


def print_group_table(groups: dict, catalog_module, inventory_module) -> None:
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Group", style="bold", width=7)
    table.add_column("Team", width=24)
    table.add_column("Have", justify="right", width=6)
    table.add_column("Progress", width=22)

    for grp in sorted(groups.keys()):
        first = True
        for tc in groups[grp]:
            meta = catalog_module.team_meta(tc)
            prog = inventory_module.team_progress(tc)
            have = prog["have"]
            total = meta["total"]
            pct = int(have / total * 100) if total else 0
            filled = pct // 5
            bar = f"[green]{'█' * filled}[/green][dim]{'░' * (20 - filled)}[/dim]"
            grp_label = f"[bold cyan]{grp}[/bold cyan]" if first else ""
            flag = meta.get("flag", "")
            name = meta.get("team_name", tc)
            table.add_row(grp_label, f"{flag} {name}", f"{have}/{total}", bar)
            first = False

    console.print(table)


def print_missing_list(missing_codes: list[str], catalog_module) -> None:
    if not missing_codes:
        console.print("[green]No missing stickers![/green]")
        return

    by_team: dict[str, list] = {}
    for code in missing_codes:
        sticker = catalog_module.by_code(code)
        if sticker:
            tc = sticker.get("team_code", "?")
            by_team.setdefault(tc, []).append(sticker)

    for tc, stickers in sorted(by_team.items()):
        meta = catalog_module.team_meta(tc) if tc not in ("FWC", "PANINI") else {"flag": "🏆", "team_name": "FIFA WC", "group": None}
        flag = meta.get("flag", "")
        name = meta.get("team_name", tc)
        grp = meta.get("group")
        header = f"{flag} [bold]{name}[/bold]"
        if grp:
            header += f"  [dim]Group {grp}[/dim]"
        console.print(header)
        items = []
        for s in stickers:
            foil_mark = " [yellow]★foil[/yellow]" if s.get("foil") else ""
            player = s.get("player") or s.get("description", "")
            items.append(f"  [cyan]{s['display']}[/cyan] {player}{foil_mark}")
        console.print("\n".join(items))
        console.print()


def print_extras_list(extras: list[dict], catalog_module) -> None:
    if not extras:
        console.print("[dim]No extras yet.[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Code", style="cyan", width=8)
    table.add_column("Team", width=20)
    table.add_column("Player / Description", width=28)
    table.add_column("Qty", justify="right", width=5)

    for item in sorted(extras, key=lambda x: x["code"]):
        s = catalog_module.by_code(item["code"])
        if s:
            player = s.get("player") or s.get("description", "")
            foil = " ★" if s.get("foil") else ""
            table.add_row(
                s["display"],
                f"{s.get('flag','')} {s.get('team_name','')}",
                f"{player}{foil}",
                str(item["qty"]),
            )
    console.print(table)
