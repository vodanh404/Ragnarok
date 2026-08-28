"""
Tạo mã Barcode Code128 (port từ modules/Barcode.py).
"""

from pathlib import Path

from rich.prompt import Prompt

from ui.console import console
from output_paths import output_path


def feature_barcode() -> None:
    """Tạo mã vạch Code128."""
    console.print("[bold cyan]═══ TẠO MÃ BARCODE (Code128) ═══[/bold cyan]\n")
    data = Prompt.ask(
        "[bold]Nhập dữ liệu barcode[/bold]",
        default="PRODUCT-SKU-2026",
    ).strip()
    if not data:
        console.print("[red]Dữ liệu trống. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    filename = Prompt.ask(
        "[bold]Tên file xuất (không cần đuôi)[/bold]",
        default="barcode_code128",
    ).strip() or "barcode_code128"

    try:
        import barcode
        from barcode.writer import ImageWriter

        code = barcode.get("code128", data, writer=ImageWriter())
        target = output_path("barcode", Path(filename).name, "barcode_code128")
        saved = code.save(str(target.with_suffix("")))
        console.print(f"[bold green]✓ Đã lưu barcode:[/bold green] {Path(saved).resolve()}")
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install python-barcode pillow[/yellow]"
        )
    except Exception as exc:
        console.print(f"[red]Lỗi tạo barcode:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_barcode
