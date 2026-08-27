"""
Chụp màn hình (ý tưởng từ qxresearch ScreenShot).
Dùng Pillow ImageGrab – đã có trong requirements.
"""

from datetime import datetime
from pathlib import Path

from rich.prompt import Confirm, Prompt

from ui.console import console
from output_paths import output_path


def feature_screenshot() -> None:
    """Chụp toàn màn hình và lưu PNG/JPG."""
    console.print("[bold cyan]═══ CHỤP MÀN HÌNH ═══[/bold cyan]\n")

    try:
        from PIL import ImageGrab
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install Pillow[/yellow]"
        )
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    save_dir = output_path("screenshots", "_folder_marker").parent

    fmt = Prompt.ask(
        "[bold]Định dạng[/bold]",
        choices=["png", "jpg"],
        default="png",
    )
    default_name = f"shot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
    name = Prompt.ask(
        "[bold]Tên tệp[/bold]",
        default=default_name,
    ).strip() or default_name
    if not name.lower().endswith(f".{fmt}"):
        name = f"{name}.{fmt}"
    out_path = output_path("screenshots", name, default_name)
    if out_path.exists():
        if not Confirm.ask(f"[yellow]Tệp đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

    delay_raw = Prompt.ask(
        "[bold]Độ trễ (giây) trước khi chụp[/bold]",
        default="0",
    ).strip() or "0"
    try:
        delay = max(0, int(delay_raw))
    except ValueError:
        delay = 0

    if delay > 0:
        import time

        console.print(f"[yellow]Chụp sau {delay}s...[/yellow]")
        time.sleep(delay)

    try:
        # all_screens=True nếu Pillow hỗ trợ (multi-monitor)
        try:
            img = ImageGrab.grab(all_screens=True)
        except TypeError:
            img = ImageGrab.grab()

        if fmt == "jpg":
            img = img.convert("RGB")
            img.save(out_path, quality=92)
        else:
            img.save(out_path)

        console.print(
            f"[bold green]✓ Đã chụp:[/bold green] {out_path.resolve()} "
            f"({img.size[0]}x{img.size[1]})"
        )
    except OSError as exc:
        console.print(
            f"[red]Không chụp được màn hình:[/red] {exc}\n"
            "[dim]Trên Linux headless/Wayland có thể cần: "
            "python3-xlib, scrot, hoặc chạy trong session có DISPLAY.[/dim]"
        )
    except Exception as exc:
        console.print(f"[red]Lỗi chụp màn hình:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
