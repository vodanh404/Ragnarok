"""
Tra cứu Pokémon / thẻ bài (port từ module/pokemon.py + PokeAPI fallback).
"""

from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ui.console import console


def feature_pokemon() -> None:
    """Tra cứu thông tin Pokémon hoặc thẻ TCG."""
    console.print("[bold cyan]═══ POKÉDEX / TCG ═══[/bold cyan]\n")
    mode = Prompt.ask(
        "Chế độ ([cyan]1[/cyan]=Pokémon species, [cyan]2[/cyan]=TCG Card ID)",
        choices=["1", "2"],
        default="1",
    )

    if mode == "1":
        _lookup_species()
    else:
        _lookup_tcg_card()

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")


def _lookup_species() -> None:
    name = Prompt.ask("[bold]Tên / ID Pokémon[/bold]", default="pikachu").strip().lower()
    if not name:
        console.print("[red]Tên trống.[/red]")
        return

    try:
        import requests
    except ImportError:
        console.print("[red]Cần:[/red] [yellow]pip install requests[/yellow]")
        return

    url = f"https://pokeapi.co/api/v2/pokemon/{name}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            console.print(f"[red]Không tìm thấy '{name}'.[/red]")
            return
        data = resp.json()

        types = ", ".join(t["type"]["name"] for t in data["types"])
        abilities = ", ".join(a["ability"]["name"] for a in data["abilities"])
        stats_table = Table(title="Base Stats", border_style="yellow")
        stats_table.add_column("Stat", style="cyan")
        stats_table.add_column("Value", justify="right")
        for s in data["stats"]:
            stats_table.add_row(s["stat"]["name"], str(s["base_stat"]))

        info = (
            f"[bold]{data['name'].title()}[/bold]  (#{data['id']})\n"
            f"Chiều cao : {data['height'] / 10} m\n"
            f"Cân nặng  : {data['weight'] / 10} kg\n"
            f"Hệ        : {types}\n"
            f"Ability   : {abilities}"
        )
        console.print(Panel(info, title="Pokémon", border_style="green"))
        console.print(stats_table)
    except Exception as exc:
        console.print(f"[red]Lỗi:[/red] {exc}")


def _lookup_tcg_card() -> None:
    card_id = Prompt.ask(
        "[bold]Card ID (vd: swsh3-136)[/bold]",
        default="swsh3-136",
    ).strip()
    if not card_id:
        return

    try:
        from tcgdexsdk import TCGdex, Language
        from tcgdexsdk.enums import Quality, Extension
    except ImportError:
        console.print(
            "[red]Thiếu tcgdex-sdk. Cài đặt:[/red] "
            "[yellow]pip install tcgdex-sdk[/yellow]\n"
            "[dim]Hoặc dùng chế độ 1 (PokeAPI) không cần package này.[/dim]"
        )
        return

    try:
        tcgdex = TCGdex(Language.EN)
        card = tcgdex.card.getSync(card_id)
        if not card:
            console.print("[red]Không tìm thấy thẻ.[/red]")
            return

        lines = [
            f"[bold]{card.name}[/bold]",
            f"ID      : {card.id}",
            f"Local ID: {getattr(card, 'localId', 'N/A')}",
            f"Illustrator: {getattr(card, 'illustrator', 'N/A')}",
            f"Rarity  : {getattr(card, 'rarity', 'N/A')}",
            f"HP      : {getattr(card, 'hp', 'N/A')}",
            f"Types   : {getattr(card, 'types', 'N/A')}",
        ]
        if hasattr(card, "set") and card.set:
            lines.append(f"Set     : {card.set.name} ({card.set.id})")

        if hasattr(card, "attacks") and card.attacks:
            lines.append("\n[bold]Attacks[/bold]")
            for atk in card.attacks:
                cost = ", ".join(atk.cost) if getattr(atk, "cost", None) else "—"
                dmg = getattr(atk, "damage", "N/A")
                lines.append(f"  • {atk.name} [{cost}] → {dmg}")

        console.print(Panel("\n".join(lines), title="TCG Card", border_style="magenta"))

        try:
            img_url = card.get_image_url(quality=Quality.HIGH, extension=Extension.PNG)
            console.print(f"[dim]Ảnh:[/dim] {img_url}")
        except Exception:
            pass
    except Exception as exc:
        console.print(f"[red]Lỗi TCG:[/red] {exc}")

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_pokemon
