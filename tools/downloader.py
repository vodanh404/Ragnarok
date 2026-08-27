"""
Tải Video / Nhạc từ YouTube (port từ module/video_music_dowloader.py).
"""

import shutil
from pathlib import Path
from urllib.parse import urlparse

from rich.prompt import Prompt

from ui.console import console
from output_paths import output_dir


def _ffmpeg_available() -> bool:
    """Kiểm tra FFmpeg có trong PATH (system dependency, không cài bằng pip)."""
    return shutil.which("ffmpeg") is not None


def _is_plausible_url(url: str) -> bool:
    """Kiểm tra URL cơ bản trước khi gọi yt-dlp."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def feature_downloader() -> None:
    """Tải video hoặc audio bằng yt-dlp."""
    console.print("[bold cyan]═══ TẢI VIDEO VÀ NHẠC ═══[/bold cyan]\n")

    url = Prompt.ask("[bold]Địa chỉ video[/bold]").strip()
    if not url:
        console.print("[red]Địa chỉ web trống. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    if not _is_plausible_url(url):
        console.print(
            "[red]Địa chỉ web không hợp lệ.[/red] "
            "Cần dạng https://... (ví dụ YouTube, Vimeo, ...)."
        )
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    mode = Prompt.ask(
        "[bold]Chế độ[/bold] ([cyan]1[/cyan]=Video MP4, [cyan]2[/cyan]=Âm thanh MP3)",
        choices=["1", "2"],
        default="1",
    )
    requested_dir = Prompt.ask("[bold]Thư mục con trong output/downloads[/bold]", default="").strip()
    if requested_dir:
        safe_dir = Path(requested_dir.replace("\\", "/")).name.replace("/", "_")[:120].strip(" .")
        if not safe_dir or safe_dir in {".", ".."}:
            safe_dir = "downloads"
        out_dir = output_dir("downloads") / safe_dir
    else:
        out_dir = output_dir("downloads")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        console.print(f"[red]Không tạo được thư mục lưu:[/red] {exc}")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    outtmpl = str(out_dir / "%(title)s.%(ext)s")

    try:
        import yt_dlp
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install yt-dlp[/yellow]"
        )
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    # Âm thanh MP3 và merge video+audio đều cần FFmpeg
    needs_ffmpeg = True
    if not _ffmpeg_available():
        console.print(
            "[bold yellow]⚠ FFmpeg chưa được cài hoặc không có trong PATH.[/bold yellow]\n"
            "[dim]yt-dlp cần FFmpeg để ghép video/audio hoặc chuyển MP3.[/dim]\n"
            "Cài nhanh:\n"
            "  • Ubuntu/Debian: [cyan]sudo apt install ffmpeg[/cyan]\n"
            "  • macOS:         [cyan]brew install ffmpeg[/cyan]\n"
            "  • Windows:       tải từ https://ffmpeg.org/download.html "
            "và thêm vào PATH\n"
        )
        if mode == "2":
            console.print(
                "[red]Chế độ Âm thanh MP3 bắt buộc FFmpeg. Hủy tải.[/red]"
            )
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return
        # Mode video: vẫn thử, nhưng cảnh báo có thể fail khi cần merge
        cont = Prompt.ask(
            "Vẫn thử tải video (có thể lỗi khi cần ghép stream)?",
            choices=["y", "n"],
            default="n",
        )
        if cont == "n":
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return
        needs_ffmpeg = False

    if mode == "1":
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestvideo+bestaudio/best" if needs_ffmpeg else "best",
            "merge_output_format": "mp4",
            "noplaylist": True,
        }
        label = "video"
    else:
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "noplaylist": True,
        }
        label = "audio"

    console.print(f"[yellow]Đang tải {label}...[/yellow]")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        console.print(f"[bold green]✓ Tải xong →[/bold green] {out_dir.resolve()}")
    except yt_dlp.utils.DownloadError as exc:
        err = str(exc).lower()
        if "private" in err:
            console.print("[red]Video riêng tư – không tải được.[/red]")
        elif "deleted" in err or "unavailable" in err or "not available" in err:
            console.print("[red]Video đã bị xóa hoặc không khả dụng.[/red]")
        elif "ffmpeg" in err:
            console.print(
                "[red]Lỗi FFmpeg khi xử lý file.[/red] "
                "Cài FFmpeg và đảm bảo có trong PATH."
            )
        else:
            console.print(f"[red]Lỗi tải:[/red] {exc}")
    except Exception as exc:
        console.print(f"[red]Lỗi tải:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
