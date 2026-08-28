"""
Tùy chỉnh giao diện chương trình: màu chữ, kiểu chữ (đậm/nghiêng/gạch chân...)
và màu nền cho toàn bộ RAGNAROK CONTROL CENTER.

Mỗi lựa chọn (màu chữ / kiểu chữ / màu nền) được áp dụng NGAY LẬP TỨC lên
console dùng chung ngay khi vừa chọn xong -- không cần đợi đến bước xác nhận
cuối, và không cần khởi động lại chương trình. Chỉ khi người dùng xác nhận
"Lưu" thì lựa chọn đó mới được ghi xuống config/theme.json để tự động dùng
lại ở lần chạy sau; nếu hủy, giao diện trước đó sẽ được khôi phục lại.

Quy tắc bắt buộc: màu chữ và màu nền KHÔNG được trùng nhau.
"""

from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from theme import (
    BACKGROUND_CHOICES,
    COLOR_CHOICES,
    FONT_STYLE_CHOICES,
    Theme,
    save_theme,
)
from ui.console import apply_theme, console, get_current_theme

TOOL_NAME = "Tùy chỉnh giao diện (màu chữ / kiểu chữ / nền)"
CATEGORY = "Cài đặt / Settings"


def _pick(title: str, choices: dict, current_key: str) -> str:
    """Hiện một bảng lựa chọn đánh số và trả về key mà người dùng chọn."""
    keys = list(choices.keys())
    table = Table(title=title, border_style="bold magenta", header_style="bold cyan")
    table.add_column("STT", justify="center", style="bold magenta")
    table.add_column("Tuỳ chọn", style="white")
    for i, key in enumerate(keys, start=1):
        mark = "  [dim](đang dùng)[/dim]" if key == current_key else ""
        table.add_row(str(i), f"{choices[key]}{mark}")
    console.print(table)

    idx = Prompt.ask(
        "[bold magenta]Chọn số[/bold magenta]",
        choices=[str(i) for i in range(1, len(keys) + 1)],
        default="1",
        show_choices=False,
    )
    return keys[int(idx) - 1]


def _preview(theme: Theme) -> None:
    """In thử một khối văn bản theo đúng theme sắp áp dụng, trước khi lưu."""
    primary = theme.primary_style()
    accent = theme.accent_style()
    console.print()
    console.print(
        Panel(
            f"[{primary}]RAGNAROK CONTROL CENTER[/{primary}]\n"
            f"[{accent}]Đây là bản xem trước giao diện của bạn.[/{accent}]\n"
            f"Chữ thường không gắn tag màu sẽ trông như thế này.",
            title="Xem trước / Preview",
            border_style=primary,
            style=theme.console_base_style(),
            expand=False,
        )
    )
    console.print()


def run() -> None:
    console.print("[bold cyan]═══ TÙY CHỈNH GIAO DIỆN ═══[/bold cyan]\n")

    original = get_current_theme()
    console.print(
        "Hiện tại: "
        f"màu chữ = [bold]{COLOR_CHOICES.get(original.fg_color, original.fg_color)}[/bold], "
        f"kiểu chữ = [bold]{FONT_STYLE_CHOICES.get(original.font_style, original.font_style)}[/bold], "
        f"màu nền = [bold]{BACKGROUND_CHOICES.get(original.bg_color, original.bg_color)}[/bold]\n"
    )
    console.print(
        "[dim]Mỗi lựa chọn bên dưới sẽ đổi giao diện ngay lập tức để bạn xem trực tiếp "
        "(chưa lưu cho đến bước xác nhận cuối).[/dim]\n"
    )

    if Confirm.ask("[bold]Khôi phục giao diện mặc định (chữ đỏ đậm, nền mặc định)?[/bold]", default=False):
        working = Theme()
        apply_theme(working)  # áp ngay để thấy hiệu ứng tức thì
    else:
        # Bản nháp: mỗi bước chọn xong sẽ apply_theme() ngay, nên các bảng/màn
        # hình tiếp theo trong chính phiên làm việc này đã đổi màu theo lựa
        # chọn mới nhất -- không cần chờ đến cuối, càng không cần khởi động
        # lại chương trình.
        working = Theme(
            fg_color=original.fg_color,
            font_style=original.font_style,
            bg_color=original.bg_color,
        )

        working.fg_color = _pick("① CHỌN MÀU CHỮ", COLOR_CHOICES, working.fg_color)
        apply_theme(working)

        working.font_style = _pick("② CHỌN KIỂU CHỮ", FONT_STYLE_CHOICES, working.font_style)
        apply_theme(working)

        while True:
            bg = _pick("③ CHỌN MÀU NỀN", BACKGROUND_CHOICES, working.bg_color)
            if bg != "default" and bg.lower() == working.fg_color.lower():
                console.print(
                    "\n[bold red]✗ Màu nền không được trùng với màu chữ. "
                    "Vui lòng chọn một màu nền khác.[/bold red]\n"
                )
                continue
            working.bg_color = bg
            apply_theme(working)  # áp ngay để thấy màu nền mới
            break

    _preview(working)

    if Confirm.ask("[bold]Lưu giao diện này để dùng cho cả những lần chạy sau?[/bold]", default=True):
        save_theme(working)
        console.print(
            "[bold green]✓ Đã lưu. Giao diện đã được áp dụng ngay cho toàn bộ chương trình "
            "(không cần khởi động lại).[/bold green]"
        )
    else:
        apply_theme(original)  # chưa lưu -> khôi phục lại giao diện trước đó
        console.print("[yellow]Đã hủy, khôi phục lại giao diện trước đó.[/yellow]")

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
