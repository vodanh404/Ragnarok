"""
Bảng tuần hoàn – tra cứu nguyên tố (port logic mendeleev từ modules/periodic_table.py).
"""

from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ui.console import console

_FALLBACK = {
    "H": ("Hydrogen", 1, 1.008, "Nonmetal"),
    "He": ("Helium", 2, 4.003, "Noble gas"),
    "Li": ("Lithium", 3, 6.94, "Alkali metal"),
    "C": ("Carbon", 6, 12.011, "Nonmetal"),
    "N": ("Nitrogen", 7, 14.007, "Nonmetal"),
    "O": ("Oxygen", 8, 15.999, "Nonmetal"),
    "Na": ("Sodium", 11, 22.990, "Alkali metal"),
    "Mg": ("Magnesium", 12, 24.305, "Alkaline earth"),
    "Al": ("Aluminium", 13, 26.982, "Post-transition"),
    "Si": ("Silicon", 14, 28.085, "Metalloid"),
    "P": ("Phosphorus", 15, 30.974, "Nonmetal"),
    "S": ("Sulfur", 16, 32.06, "Nonmetal"),
    "Cl": ("Chlorine", 17, 35.45, "Halogen"),
    "K": ("Potassium", 19, 39.098, "Alkali metal"),
    "Ca": ("Calcium", 20, 40.078, "Alkaline earth"),
    "Fe": ("Iron", 26, 55.845, "Transition metal"),
    "Cu": ("Copper", 29, 63.546, "Transition metal"),
    "Zn": ("Zinc", 30, 65.38, "Transition metal"),
    "Ag": ("Silver", 47, 107.87, "Transition metal"),
    "Au": ("Gold", 79, 196.97, "Transition metal"),
    "Hg": ("Mercury", 80, 200.59, "Transition metal"),
    "Pb": ("Lead", 82, 207.2, "Post-transition"),
    "U": ("Uranium", 92, 238.03, "Actinide"),
}


def feature_element() -> None:
    """Tra cứu nguyên tố theo ký hiệu hoặc số hiệu nguyên tử."""
    console.print("[bold cyan]═══ BẢNG TUẦN HOÀN ═══[/bold cyan]\n")
    console.print(
        "[dim]Nhập ký hiệu (H, Fe, Au…) hoặc số hiệu nguyên tử. "
        "Gõ [yellow]list[/yellow] để xem mẫu, [yellow]q[/yellow] thoát.[/dim]\n"
    )

    while True:
        query = Prompt.ask("[bold]Nguyên tố[/bold]").strip()
        if not query or query.lower() in ("q", "quit", "exit"):
            break
        if query.lower() == "list":
            _print_sample()
            continue

        if _try_mendeleev(query):
            continue
        _try_fallback(query)

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")


def _try_mendeleev(query: str) -> bool:
    try:
        from mendeleev import element
    except ImportError:
        return False

    try:
        if query.isdigit():
            el = element(int(query))
        else:
            el = element(query.capitalize() if len(query) > 1 else query.upper())

        info = (
            f"[bold]{el.name} ({el.symbol})[/bold]\n\n"
            f"Số hiệu Z     : {el.atomic_number}\n"
            f"Khối lượng    : {el.atomic_weight}\n"
            f"Nhóm / Chu kỳ : {el.group_id} / {el.period}\n"
            f"Block         : {el.block}-block\n"
            f"Trạng thái    : {getattr(el, 'series', 'N/A')}\n"
            f"Cấu hình e    : {getattr(el, 'econf', 'N/A')}\n"
            f"Điểm nóng chảy: {getattr(el, 'melting_point', 'N/A')} K\n"
            f"Điểm sôi      : {getattr(el, 'boiling_point', 'N/A')} K"
        )
        console.print(Panel(info, title="Nguyên tố", border_style="green"))
        return True
    except Exception as exc:
        console.print(f"[yellow]mendeleev:[/yellow] {exc} → thử fallback...")
        return False


def _try_fallback(query: str) -> None:
    key = query.upper() if len(query) <= 2 else query.capitalize()
    if query.isdigit():
        for sym, (name, z, mass, series) in _FALLBACK.items():
            if z == int(query):
                key = sym
                break
        else:
            console.print(
                "[red]Không có trong dữ liệu fallback. "
                "Cài mendeleev để tra đầy đủ.[/red]"
            )
            return

    if key not in _FALLBACK:
        for sym, (name, z, mass, series) in _FALLBACK.items():
            if name.lower() == query.lower():
                key = sym
                break
        else:
            console.print(
                f"[red]Không tìm thấy '{query}'.[/red] "
                "[dim]Cài [yellow]pip install mendeleev[/yellow] để có đủ 118 nguyên tố.[/dim]"
            )
            return

    name, z, mass, series = _FALLBACK[key]
    info = (
        f"[bold]{name} ({key})[/bold]\n\n"
        f"Số hiệu Z  : {z}\n"
        f"Khối lượng : {mass}\n"
        f"Nhóm       : {series}"
    )
    console.print(Panel(info, title="Nguyên tố (fallback)", border_style="yellow"))


def _print_sample() -> None:
    table = Table(title="Một số nguyên tố mẫu", border_style="cyan")
    table.add_column("Ký hiệu", style="bold")
    table.add_column("Tên")
    table.add_column("Z", justify="right")
    table.add_column("Mass", justify="right")
    for sym, (name, z, mass, _) in list(_FALLBACK.items())[:12]:
        table.add_row(sym, name, str(z), str(mass))
    console.print(table)

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_element
