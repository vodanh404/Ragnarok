"""Render images directly inside ANSI-compatible terminals using truecolor blocks."""
from __future__ import annotations

from pathlib import Path
from rich.prompt import Prompt
from rich.text import Text
from PIL import Image, ImageOps
from ui.console import console
from ui.file_picker import choose_files


def _ansi_image(img: Image.Image, width: int) -> str:
    img = ImageOps.exif_transpose(img).convert("RGB")
    ratio = img.height / max(1, img.width)
    # One terminal character is roughly twice as tall as it is wide.
    height = max(1, int(width * ratio * 0.48))
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    # Resize exactly to target-ish width while preserving aspect ratio.
    lines = []
    px = img.load()
    for y in range(0, img.height - 1, 2):
        line = []
        for x in range(img.width):
            r1, g1, b1 = px[x, y]
            r2, g2, b2 = px[x, min(y + 1, img.height - 1)]
            line.append(f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀")
        lines.append("".join(line) + "\x1b[0m")
    return "\n".join(lines)


def feature_terminal_image() -> None:
    selected = choose_files(
        title="Chọn ảnh để hiển thị",
        filetypes=[("Hình ảnh", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif"), ("Tất cả tệp", "*.*")],
    )
    if not selected:
        console.print("[dim]Không chọn ảnh.[/dim]")
        Prompt.ask("Nhấn phím xác nhận để quay lại")
        return
    p = selected[0]
    if not p.is_file():
        console.print("[red]Không tìm thấy file ảnh.[/red]")
        Prompt.ask("Nhấn phím xác nhận để quay lại")
        return
    try:
        width = int(Prompt.ask("Chiều rộng terminal", default="70"))
        width = max(10, min(width, 180))
        with Image.open(p) as img:
            console.print(f"[bold cyan]{p.name}[/bold cyan]  {img.width}×{img.height}")
            # Print raw ANSI so cửa sổ lệnh Windows / ANSI terminals can render truecolor.
            print(_ansi_image(img, width))
            console.print("[dim]Mẹo: cửa sổ lệnh Windows hỗ trợ ANSI/truecolor tốt hơn cửa sổ lệnh cổ điển.[/dim]")
    except Exception as exc:
        console.print(f"[red]Không thể hiển thị ảnh: {exc}[/red]")
    Prompt.ask("Nhấn phím xác nhận để quay lại")
