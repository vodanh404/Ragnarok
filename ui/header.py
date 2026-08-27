"""
Đầu trang, biểu ngữ và tiện ích màn hình.
"""

import os
from rich.panel import Panel

from .console import console

BANNER = """[bold red]
██████╗  █████╗  ██████╗ ███╗   ██╗█████╗ ██████╗  ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔════╝ ████╗  ██║██╔══██╗██╔══██╗██╔═══██╗██║ ██╔╝
██████╔╝███████║██║  ███╗██╔██╗ ██║███████║██████╔╝██║   ██║█████╔╝ 
██╔══██╗██╔══██║██║   ██║██║╚██╗██║██╔══██║██╔══██╗██║   ██║██╔═██╗ 
██║  ██║██║  ██║╚██████╔╝██║ ╚████║██║  ██║██║  ██║╚██████╔╝██║  ██╗
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
[/bold red]"""


def clear_screen() -> None:
    """Xóa sạch màn hình và bộ đệm cuộn hiển thị của terminal."""
    # ANSI được hỗ trợ tốt trên Windows Terminal/PowerShell hiện đại; fallback
    # sang lệnh hệ điều hành để tương thích các terminal cũ hơn.
    try:
        console.clear()
        print("\x1b[2J\x1b[H", end="", flush=True)
    except Exception:
        os.system("cls" if os.name == "nt" else "clear")


def show_header() -> None:
    """Clear screen and print banner + title panel."""
    clear_screen()
    console.print(BANNER)
    console.print(
        Panel(
            "[bold red]TRUNG TÂM ĐIỀU KHIỂN RAGNAROK[/bold red] | [bold yellow] Poket_studio • phiên bản 1.1.1[/bold yellow]",
            border_style="bold red",
            expand=False,
        )
    )
