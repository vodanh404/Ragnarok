"""
Tạo mật khẩu ngẫu nhiên an toàn (nâng cấp từ random.randint gốc).
"""

import secrets
import string

from rich.prompt import Prompt

from ui.console import console


def feature_password() -> None:
    """Sinh mật khẩu ngẫu nhiên an toàn."""
    console.print("[bold cyan]═══ TẠO MẬT KHẨU ═══[/bold cyan]\n")

    length_str = Prompt.ask("[bold]Độ dài[/bold]", default="16")
    try:
        length = max(4, min(128, int(length_str)))
    except ValueError:
        length = 16

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    console.print(f"\n[bold yellow]Mật khẩu:[/bold yellow] {password}\n")
    Prompt.ask("[dim]Nhấn Enter để quay lại...[/dim]")

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_password
