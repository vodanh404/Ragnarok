"""
Tách audio từ file video local (ý tưởng Extract mp3 from mp4 – qxresearch).
Dùng FFmpeg (system), không phụ thuộc moviepy.
"""

import shutil
import subprocess
from pathlib import Path

from rich.prompt import Confirm, Prompt

from ui.console import console
from output_paths import output_path
from ui.file_picker import choose_files

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v", ".wmv"}


def feature_audio_extract() -> None:
    """Tách track audio từ video → MP3/WAV/AAC."""
    console.print("[bold cyan]═══ TÁCH AUDIO TỪ VIDEO ═══[/bold cyan]\n")

    if not shutil.which("ffmpeg"):
        console.print(
            "[bold yellow]⚠ FFmpeg chưa có trong PATH.[/bold yellow]\n"
            "Cài:\n"
            "  • Ubuntu/Debian: [cyan]sudo apt install ffmpeg[/cyan]\n"
            "  • macOS:         [cyan]brew install ffmpeg[/cyan]\n"
            "  • Windows:       https://ffmpeg.org/download.html\n"
        )
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    selected = choose_files(
        title="Chọn file video",
        filetypes=[("Video", "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;*.m4v;*.wmv"), ("All files", "*.*")],
    )
    if not selected:
        console.print("[dim]Không chọn file. Hủy.[/dim]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return
    src_path = selected[0]
    if not src_path.is_file():
        console.print(f"[red]Không tìm thấy file:[/red] {src_path}")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    fmt = Prompt.ask(
        "[bold]Định dạng xuất[/bold]",
        choices=["mp3", "wav", "aac", "m4a"],
        default="mp3",
    )
    default_out = f"{src_path.stem}.{fmt}"
    out_name = Prompt.ask(
        "[bold]Tên file xuất[/bold]",
        default=default_out,
    ).strip() or default_out
    if not out_name.lower().endswith(f".{fmt}"):
        out_name = f"{out_name}.{fmt}"
    out_path = output_path("audio", out_name, default_out)
    if out_path.exists():
        if not Confirm.ask(f"[yellow]File đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
            return


    # Codec theo format
    if fmt == "mp3":
        codec_args = ["-vn", "-acodec", "libmp3lame", "-q:a", "2"]
    elif fmt == "wav":
        codec_args = ["-vn", "-acodec", "pcm_s16le"]
    elif fmt in ("aac", "m4a"):
        codec_args = ["-vn", "-acodec", "aac", "-b:a", "192k"]
    else:
        codec_args = ["-vn"]

    cmd = [
        "ffmpeg",
        "-n",
        "-i",
        str(src_path),
        *codec_args,
        str(out_path),
    ]
    console.print(f"[yellow]Đang tách audio...[/yellow] ({src_path.name} → {out_path.name})")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip().splitlines()
            tail = "\n".join(err[-8:]) if err else "FFmpeg thất bại"
            console.print(f"[red]FFmpeg lỗi:[/red]\n{tail}")
        elif not out_path.is_file() or out_path.stat().st_size == 0:
            console.print(
                "[red]Không tạo được file audio (video có thể không có track audio).[/red]"
            )
        else:
            size_kb = out_path.stat().st_size / 1024
            console.print(
                f"[bold green]✓ Đã lưu:[/bold green] {out_path.resolve()} "
                f"({size_kb:.1f} KB)"
            )
    except subprocess.TimeoutExpired:
        console.print("[red]Hết thời gian chờ khi chạy FFmpeg.[/red]")
    except FileNotFoundError:
        console.print("[red]Không tìm thấy lệnh ffmpeg trong PATH.[/red]")
    except Exception as exc:
        console.print(f"[red]Lỗi:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_audio_extract
