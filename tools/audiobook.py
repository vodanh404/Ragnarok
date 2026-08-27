"""
Audiobook: đọc tệp văn bản thành giọng nói (ý tưởng qxresearch audiobook).
Dùng gTTS (đã có) – xuất MP3; hỗ trợ file dài theo chunk.
"""

from pathlib import Path
import shutil
import subprocess

from rich.prompt import Confirm, Prompt

from ui.console import console
from output_paths import output_path
from ui.file_picker import choose_files

# gTTS giới hạn độ dài request – chia chunk an toàn
CHUNK_SIZE = 3000  # an toàn hơn cho UTF-8/Vietnamese


def feature_audiobook() -> None:
    """Đọc file .txt → MP3 bằng gTTS."""
    console.print("[bold cyan]═══ AUDIOBOOK (TEXT → GIỌNG NÓI) ═══[/bold cyan]\n")

    selected = choose_files(title="Chọn tệp văn bản TXT", filetypes=[("Tệp văn bản", "*.txt"), ("Tất cả tệp", "*.*")])
    if not selected:
        console.print("[dim]Không chọn file. Hủy.[/dim]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return
    src_path = selected[0]
    if not src_path.is_file():
        console.print(f"[red]Không tìm thấy file:[/red] {src_path}")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    try:
        text = src_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        console.print(f"[red]Không đọc được file:[/red] {exc}")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    if not text:
        console.print("[red]Tệp trống.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    lang = Prompt.ask("[bold]Ngôn ngữ[/bold]", default="vi").strip() or "vi"
    slow = Confirm.ask("Đọc chậm?", default=False)
    default_out = f"{src_path.stem}_audiobook.mp3"
    out_name = Prompt.ask(
        "[bold]Tên tệp xuất[/bold]",
        default=default_out,
    ).strip() or default_out
    if not out_name.lower().endswith(".mp3"):
        out_name += ".mp3"
    out_path = output_path("audiobook", out_name, "audiobook.mp3").expanduser()
    if out_path.exists():
        if not Confirm.ask(f"[yellow]Tệp đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

    try:
        from gtts import gTTS
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install gTTS[/yellow]"
        )
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    chunks = _split_text(text, CHUNK_SIZE)
    console.print(
        f"[yellow]Đang tạo audiobook...[/yellow] "
        f"({len(text)} ký tự, {len(chunks)} phần)"
    )

    try:
        if out_path.parent != Path("."):
            out_path.parent.mkdir(parents=True, exist_ok=True)

        if len(chunks) == 1:
            tts = gTTS(text=chunks[0], lang=lang, slow=slow)
            tts.save(str(out_path))
        else:
            # Ghép nhiều phần MP3 (gTTS mỗi request một file)
            import tempfile

            part_paths: list[Path] = []
            with tempfile.TemporaryDirectory() as tmp:
                tmp_dir = Path(tmp)
                for i, chunk in enumerate(chunks):
                    part = tmp_dir / f"part_{i:03d}.mp3"
                    console.print(f"  [dim]Phần {i + 1}/{len(chunks)}...[/dim]")
                    gTTS(text=chunk, lang=lang, slow=slow).save(str(part))
                    part_paths.append(part)
                _concat_mp3(part_paths, out_path)

        size_kb = out_path.stat().st_size / 1024
        console.print(
            f"[bold green]✓ Đã lưu:[/bold green] {out_path.resolve()} ({size_kb:.1f} KB)"
        )

        if Confirm.ask("Phát ngay?", default=False):
            from tools.tts import _play_audio

            _play_audio(out_path)
    except Exception as exc:
        msg = str(exc).lower()
        if "lang" in msg or "language" in msg:
            console.print(f"[red]Ngôn ngữ không hỗ trợ:[/red] {lang}")
        elif "network" in msg or "connection" in msg or "urlopen" in msg:
            console.print("[red]Lỗi mạng khi gọi gTTS. Kiểm tra Internet.[/red]")
        else:
            console.print(f"[red]Lỗi audiobook:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")


def _split_text(text: str, size: int) -> list[str]:
    """Chia text theo khoảng trắng gần mốc size."""
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # lùi về khoảng trắng gần nhất
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        start = end
        while start < len(text) and text[start].isspace():
            start += 1
    return [c for c in chunks if c]


def _concat_mp3(parts: list[Path], out: Path) -> None:
    """Ghép MP3 bằng FFmpeg concat demuxer để tránh nối raw binary MP3."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Cần FFmpeg để ghép audiobook nhiều phần. Hãy cài FFmpeg và thêm vào PATH.")

    # concat demuxer đọc danh sách file và FFmpeg xử lý container/frame đúng cách.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        list_file = Path(tmp) / "concat.txt"
        lines = []
        for part in parts:
            safe = part.resolve().as_posix().replace("'", "'\\''")
            lines.append(f"file '{safe}'")
        list_file.write_text("\n".join(lines), encoding="utf-8")
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", "-y", str(out)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or "FFmpeg ghép MP3 thất bại").strip())
