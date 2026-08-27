"""
Text-to-Speech bằng gTTS (port từ module/text_to_speech.py).
"""

from pathlib import Path

from rich.prompt import Confirm, Prompt

from ui.console import console
from output_paths import output_path


def feature_tts() -> None:
    """Chuyển văn bản thành file MP3."""
    console.print("[bold cyan]═══ CHUYỂN VĂN BẢN THÀNH GIỌNG NÓI ═══[/bold cyan]\n")

    text = Prompt.ask("[bold]Nhập văn bản cần đọc[/bold]")
    if not text.strip():
        console.print("[red]Văn bản trống. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    lang = Prompt.ask("[bold]Ngôn ngữ[/bold]", default="vi")
    slow = Confirm.ask("Đọc chậm?", default=False)
    out_name = Prompt.ask(
        "[bold]Tên tệp xuất[/bold]",
        default="output.mp3",
    ).strip() or "output.mp3"
    if not out_name.endswith(".mp3"):
        out_name += ".mp3"
    out_path = output_path("audio", out_name, "output.mp3")
    if out_path.exists():
        if not Confirm.ask(f"[yellow]Tệp đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
            return

    try:
        from gtts import gTTS

        console.print("[yellow]Đang tạo âm thanh...[/yellow]")
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save(str(out_path))
        console.print(f"[bold green]✓ Đã lưu:[/bold green] {out_path.resolve()}")

        if Confirm.ask("Phát ngay bằng trình phát mặc định?", default=True):
            _play_audio(out_path)
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install gTTS[/yellow]"
        )
    except Exception as exc:
        console.print(f"[red]Lỗi TTS:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")


def _play_audio(path: Path) -> None:
    """Cố gắng phát file audio trên hệ thống hiện tại."""
    import os
    import subprocess
    import sys

    try:
        if sys.platform == "darwin":
            subprocess.run(["afplay", str(path)], check=False)
        elif sys.platform.startswith("linux"):
            for player in ("xdg-open", "ffplay", "mpv", "aplay"):
                if (
                    subprocess.call(
                        ["which", player],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    == 0
                ):
                    if player == "ffplay":
                        subprocess.run(
                            ["ffplay", "-nodisp", "-autoexit", str(path)],
                            check=False,
                        )
                    else:
                        subprocess.run([player, str(path)], check=False)
                    return
            console.print("[yellow]Không tìm thấy trình phát âm thanh.[/yellow]")
        elif sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            console.print(f"[dim]Mở tệp thủ công: {path}[/dim]")
    except Exception as exc:
        console.print(f"[yellow]Không phát được âm thanh:[/yellow] {exc}")
