"""
Header, banner and screen utilities.
"""

import os

from rich.panel import Panel

from .console import console, get_current_theme

BANNER_ART = """
██████╗  █████╗  ██████╗ ███╗   ██╗█████╗ ██████╗  ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔════╝ ████╗  ██║██╔══██╗██╔══██╗██╔═══██╗██║ ██╔╝
██████╔╝███████║██║  ███╗██╔██╗ ██║███████║██████╔╝██║   ██║█████╔╝ 
██╔══██╗██╔══██║██║   ██║██║╚██╗██║██╔══██║██╔══██╗██║   ██║██╔═██╗ 
██║  ██║██║  ██║╚██████╔╝██║ ╚████║██║  ██║██║  ██║╚██████╔╝██║  ██╗
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
"""

# Giữ BANNER (không có tag màu cứng) để những chỗ khác trong project vẫn
# import được như cũ nếu cần in banner "trần".
BANNER = BANNER_ART


def clear_screen() -> None:
    """Clear terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def show_header() -> None:
    """Clear screen and print banner + title panel, theo giao diện hiện tại."""
    clear_screen()
    theme = get_current_theme()
    primary = theme.primary_style()
    accent = theme.accent_style()

    console.print(f"[{primary}]{BANNER_ART}[/{primary}]")
    console.print(
        Panel(
            f"[{primary}]RAGNAROK CONTROL CENTER[/{primary}] | "
            f"[{accent}] Poket_studio v2.0.0[/{accent}]",
            border_style=primary,
            expand=False,
        )
    )
