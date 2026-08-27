"""
Tạo mã QR Code (port từ module/qr_code.py).
"""

from pathlib import Path

from rich.prompt import Confirm, Prompt

from ui.console import console
from output_paths import output_path

# Các đuôi ảnh hợp lệ – nếu đã có thì giữ nguyên, không thêm .png
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def _normalize_output_path(filename: str) -> Path:
    """
    Chuẩn hóa tên file xuất:
    - Không có extension → thêm .png
    - Đã có .png / .jpg / .jpeg... → giữ nguyên
    - Không tạo myqr.png.png
    """
    name = filename.strip()
    if not name:
        name = "qrcode"

    path = Path(name)
    # Path.suffix trả về đuôi (có dấu chấm), so sánh không phân biệt hoa thường
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return path
    return Path(f"{name}.png")


def feature_qr() -> None:
    """Tạo mã QR từ văn bản người dùng nhập."""
    console.print("[bold cyan]═══ TẠO MÃ QR ═══[/bold cyan]\n")
    data = Prompt.ask("[bold]Nhập nội dung cần mã hóa[/bold]")
    if not data.strip():
        console.print("[red]Nội dung trống. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    filename = Prompt.ask(
        "[bold]Tên file xuất[/bold] (có thể kèm .png/.jpg hoặc không)",
        default="qrcode",
    ).strip() or "qrcode"

    # Chặn ký tự đường dẫn nguy hiểm / không hợp lệ
    if any(c in filename for c in ("\0",)):
        console.print("[red]Tên file không hợp lệ.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    out_path = output_path("qr", _normalize_output_path(filename).name, "qrcode.png")

    if out_path.exists():
        if not Confirm.ask(f"[yellow]Tệp đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

    try:
        import qrcode

        img = qrcode.make(data)
        img.save(out_path)
        console.print(f"[bold green]✓ Đã lưu mã QR:[/bold green] {out_path.resolve()}")
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install qrcode[pil][/yellow]"
        )
    except OSError as exc:
        console.print(f"[red]Lỗi ghi file:[/red] {exc}")
    except Exception as exc:
        console.print(f"[red]Lỗi tạo QR:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
