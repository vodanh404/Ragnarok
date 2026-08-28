"""
RAGNAROK CONTROL CENTER - Entry point
Poket_studio v2.0.0
"""

import os
from menu import main_menu


def main() -> None:
    """Khởi chạy ứng dụng."""
    try:
        main_menu()
    except KeyboardInterrupt:
        from ui.console import console
        console.print("\n[bold yellow]Đã dừng bởi người dùng (Ctrl+C).[/bold yellow]")
    except Exception as e:
        from ui.console import console
        console.print(f"[bold red]Lỗi không mong muốn: {e}[/bold red]")
        raise


if __name__ == "__main__":
    # Không cho Python ghi file .pyc
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    main()
