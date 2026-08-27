"""
Công cụ PDF: gộp nhiều PDF + khóa mật khẩu (ý tưởng từ qxresearch).
Dùng pypdf (thay PyPDF2/PyPDF4 đã lỗi thời).
"""

from pathlib import Path

from rich.prompt import Confirm, Prompt

from ui.console import console
from output_paths import output_path
from ui.file_picker import choose_files


def _require_pypdf():
    try:
        from pypdf import PdfReader, PdfWriter

        return PdfReader, PdfWriter
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install pypdf[/yellow]"
        )
        return None, None


def feature_pdf_merge() -> None:
    """Gộp nhiều tệp PDF thành một file."""
    console.print("[bold cyan]═══ GỘP TỆP PDF ═══[/bold cyan]\n")
    paths = [
        p for p in choose_files(
            title="Chọn các tệp PDF để gộp",
            filetypes=[("PDF", "*.pdf"), ("Tất cả tệp", "*.*")],
            multiple=True,
            prompt="Chọn cách nhập các tệp PDF",
        )
        if p.suffix.lower() == ".pdf"
    ]

    if len(paths) < 2:
        console.print("[red]Cần ít nhất 2 tệp PDF để gộp.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    out_name = Prompt.ask(
        "[bold]Tên tệp xuất[/bold]",
        default="merged.pdf",
    ).strip() or "merged.pdf"
    if not out_name.lower().endswith(".pdf"):
        out_name += ".pdf"
    out_path = output_path("pdf", out_name, "output.pdf")
    if out_path.exists():
        if not Confirm.ask(f"[yellow]Tệp đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

    PdfReader, PdfWriter = _require_pypdf()
    if PdfReader is None:
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    try:
        writer = PdfWriter()
        for p in paths:
            reader = PdfReader(str(p))
            if reader.is_encrypted:
                console.print(
                    f"[yellow]Bỏ qua PDF đã mã hóa (chưa hỗ trợ giải mã):[/yellow] {p}"
                )
                continue
            for page in reader.pages:
                writer.add_page(page)

        if len(writer.pages) == 0:
            console.print("[red]Không có trang nào để ghi (toàn bộ file bị bỏ qua).[/red]")
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

        if out_path.parent != Path("."):
            out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            writer.write(f)
        console.print(
            f"[bold green]✓ Đã gộp {len(paths)} file →[/bold green] {out_path.resolve()} "
            f"({len(writer.pages)} trang)"
        )
    except OSError as exc:
        console.print(f"[red]Lỗi ghi file:[/red] {exc}")
    except Exception as exc:
        console.print(f"[red]Lỗi gộp PDF:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")


def feature_pdf_protect() -> None:
    """Khóa PDF bằng mật khẩu (user password)."""
    console.print("[bold cyan]═══ KHÓA TỆP PDF BẰNG MẬT KHẨU ═══[/bold cyan]\n")

    selected = choose_files(
        title="Chọn tệp PDF cần khóa",
        filetypes=[("PDF", "*.pdf"), ("Tất cả tệp", "*.*")],
    )
    if not selected:
        console.print("[dim]Không chọn file. Hủy.[/dim]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return
    src_path = selected[0]
    if not src_path.is_file():
        console.print(f"[red]Không tìm thấy file:[/red] {src_path}")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return
    if src_path.suffix.lower() != ".pdf":
        console.print("[red]Tệp phải có đuôi .pdf[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    password = Prompt.ask("[bold]Mật khẩu bảo vệ[/bold]", password=True).strip()
    if not password:
        console.print("[red]Mật khẩu trống. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return
    confirm = Prompt.ask("[bold]Nhập lại mật khẩu[/bold]", password=True).strip()
    if password != confirm:
        console.print("[red]Mật khẩu không khớp. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    default_out = f"{src_path.stem}_protected.pdf"
    out_name = Prompt.ask(
        "[bold]Tên tệp xuất[/bold]",
        default=default_out,
    ).strip() or default_out
    if not out_name.lower().endswith(".pdf"):
        out_name += ".pdf"
    out_path = output_path("pdf", out_name, "output.pdf")
    if out_path.exists():
        if not Confirm.ask(f"[yellow]Tệp đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

    PdfReader, PdfWriter = _require_pypdf()
    if PdfReader is None:
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    try:
        reader = PdfReader(str(src_path))
        if reader.is_encrypted:
            console.print(
                "[red]Tệp đã được mã hóa. Giải mã trước khi khóa lại.[/red]"
            )
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)

        if out_path.parent != Path("."):
            out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            writer.write(f)
        console.print(
            f"[bold green]✓ Đã khóa PDF →[/bold green] {out_path.resolve()}"
        )
    except OSError as exc:
        console.print(f"[red]Lỗi ghi file:[/red] {exc}")
    except Exception as exc:
        console.print(f"[red]Lỗi khóa PDF:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
