"""
Menu system - Dynamic Feature Loading.

Categories and tools are no longer hard-coded here: they are discovered at
runtime from tools/ by tool_loader.discover_tools(). Adding a .py file (or a
sub-folder) under tools/ makes it show up here automatically -- see
tool_loader.py for the plugin standard every tool file must follow.
"""

from rich.table import Table
from rich.prompt import Prompt

from ui.header import show_header
from ui.console import console, get_current_theme
from tool_loader import discover_tools, DEFAULT_CATEGORY


def _print_warnings(warnings) -> None:
    """Show tools that failed to load (syntax error, missing run(), ...)."""
    if not warnings:
        return
    console.print("[bold yellow]⚠ Một số tool không tải được:[/bold yellow]")
    for file_name, reason in warnings:
        console.print(f"  [yellow]- {file_name}:[/yellow] {reason}")
    console.print()


def _run_tool(entry) -> None:
    """Run one tool. Any runtime error is caught so the app never crashes."""
    try:
        entry.run()
    except Exception as exc:  # noqa: BLE001 - a tool crashing must not kill the menu
        console.print(f"[bold red]Lỗi khi chạy '{entry.name}':[/bold red] {exc}")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")


def _category_menu(category: str) -> None:
    """List tools inside one category and dispatch the user's choice.

    Re-scans tools/ every time this screen is (re)drawn -- same as
    main_menu() -- so tools added, removed, or edited while the user is
    browsing *inside* this category show up immediately, with no need to
    back out to the main menu first."""
    while True:
        categories, warnings = discover_tools()
        entries = categories.get(category)

        if not entries:
            # Category vanished (last tool inside it was removed/renamed/
            # broke on reload) -- don't crash or show a stale empty screen,
            # just tell the user and bounce back to the main menu.
            console.print(
                f"[yellow]Danh mục '{category}' hiện không còn tool nào "
                f"(có thể vừa bị xoá/đổi tên/lỗi tải lại). Quay lại menu chính...[/yellow]"
            )
            Prompt.ask("\n[dim]Nhấn Enter để tiếp tục...[/dim]")
            return

        show_header()
        _print_warnings(warnings)
        theme = get_current_theme()
        table = Table(
            title=category.upper(),
            border_style=theme.primary_style(),
            header_style=theme.accent_style(),
        )
        table.add_column("STT", style=theme.primary_style(), justify="center")
        table.add_column("Tính năng", style=theme.accent_style())
        for i, entry in enumerate(entries, start=1):
            table.add_row(str(i), entry.name)
        table.add_row("0", "Quay lại Menu Chính")
        console.print(table)

        choice = Prompt.ask(
            f"[{theme.primary_style()}]Lựa chọn[/{theme.primary_style()}]",
            choices=[str(i) for i in range(len(entries) + 1)],
        )
        if choice == "0":
            return
        _run_tool(entries[int(choice) - 1])


def main_menu() -> None:
    """Main menu of RAGNAROK CONTROL CENTER. Re-scans tools/ every loop, so
    tools added while the app is running show up the next time this screen
    is drawn -- no restart, no manual registration needed."""
    while True:
        categories, warnings = discover_tools()
        show_header()
        _print_warnings(warnings)

        if not categories:
            console.print("[yellow]Chưa có tool nào trong thư mục tools/.[/yellow]")
            Prompt.ask("\n[dim]Nhấn Enter để thử lại...[/dim]")
            continue

        # General/"Chung" category (root-level tools) is listed first, the
        # rest are alphabetical.
        names = sorted(
            categories.keys(), key=lambda c: (c != DEFAULT_CATEGORY, c.lower())
        )

        theme = get_current_theme()
        table = Table(
            title="MENU CHÍNH",
            border_style=theme.primary_style(),
            header_style=theme.accent_style(),
        )
        table.add_column("STT", style=theme.primary_style(), justify="center")
        table.add_column("Danh mục", style=theme.accent_style())
        for i, name in enumerate(names, start=1):
            table.add_row(str(i), f"{name} ({len(categories[name])} tool)")
        table.add_row("0", "Thoát chương trình")
        console.print(table)

        choice = Prompt.ask(
            f"[{theme.primary_style()}]Lựa chọn[/{theme.primary_style()}]",
            choices=[str(i) for i in range(len(names) + 1)],
        )
        if choice == "0":
            console.print("[bold green]Tạm biệt! Hẹn gặp lại.[/bold green]")
            break

        category = names[int(choice) - 1]
        _category_menu(category)
