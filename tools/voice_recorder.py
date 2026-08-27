"""Ghi âm micro với dừng thủ công hoặc tự dừng ở giới hạn 60 phút."""

from datetime import datetime
from pathlib import Path
import sys
import time

from rich.prompt import Prompt, Confirm

from ui.console import console
from output_paths import output_path

MAX_RECORD_SECONDS = 3600


def _wait_for_enter_or_timeout(seconds: float) -> bool:
    """Chờ Enter; trả True khi hết thời gian, False khi người dùng nhấn Enter."""
    deadline = time.monotonic() + seconds
    if sys.platform == "win32":
        import msvcrt
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    return False
            time.sleep(0.05)
        return True

    import select
    while time.monotonic() < deadline:
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if ready:
            sys.stdin.readline()
            return False
    return True


def feature_voice_recorder() -> None:
    """Ghi âm đến khi nhấn Enter hoặc tự dừng sau 60 phút."""
    console.print("[bold cyan]═══ GHI ÂM ═══[/bold cyan]\n")

    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        console.print(
            "[red]Thiếu thư viện ghi âm.[/red]\n"
            "[yellow]Cài đặt: pip install sounddevice numpy[/yellow]\n"
            "[dim]Trên Linux có thể cần cài PortAudio.[/dim]"
        )
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]", default="")
        return

    sample_rate_raw = Prompt.ask("[bold]Tần số lấy mẫu[/bold]", default="44100").strip() or "44100"
    try:
        sample_rate = int(sample_rate_raw)
        if not 8000 <= sample_rate <= 192000:
            raise ValueError
    except ValueError:
        console.print("[yellow]Tần số lấy mẫu không hợp lệ, dùng 44100 Hz.[/yellow]")
        sample_rate = 44100

    default_name = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.wav"
    name = Prompt.ask("[bold]Tên tệp[/bold]", default=default_name).strip() or default_name
    if not name.lower().endswith(".wav"):
        name += ".wav"
    out_path = output_path("recordings", name, default_name)
    if out_path.exists() and not Confirm.ask(f"[yellow]Tệp đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
        console.print("[dim]Đã hủy để tránh ghi đè tệp.[/dim]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]", default="")
        return

    console.print("[dim]Nhấn phím xác nhận để BẮT ĐẦU ghi âm.[/dim]")
    Prompt.ask("", default="")
    console.print("[bold green]● ĐANG GHI ÂM[/bold green] — nhấn phím xác nhận để DỪNG.")
    console.print(f"[dim]Tự động dừng sau {MAX_RECORD_SECONDS // 60} phút.[/dim]")

    chunks = []
    total_frames = 0
    stream = None
    callback_error = []

    def callback(indata, frames, _time, status):
        nonlocal total_frames
        if status:
            callback_error.append(str(status))
        remaining = max(0, MAX_RECORD_SECONDS * sample_rate - total_frames)
        keep = min(frames, remaining)
        if keep > 0:
            chunks.append(indata[:keep].copy())
            total_frames += keep

    try:
        stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", callback=callback, blocksize=0)
        stream.start()
        auto_stopped = _wait_for_enter_or_timeout(MAX_RECORD_SECONDS)
    except KeyboardInterrupt:
        auto_stopped = False
    except Exception as exc:
        console.print(
            f"[red]Không ghi được (micro / PortAudio):[/red] {exc}\n"
            "[dim]Kiểm tra micro, quyền truy cập và thiết bị đầu vào mặc định.[/dim]"
        )
        return
    finally:
        if stream is not None:
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass

    if auto_stopped:
        console.print("[yellow]Đã tự dừng: đạt giới hạn 60 phút.[/yellow]")
    if callback_error:
        console.print(f"[dim]Cảnh báo thiết bị: {callback_error[-1]}[/dim]")

    if total_frames <= 0 or not chunks:
        console.print("[yellow]Không có dữ liệu âm thanh để lưu.[/yellow]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]", default="")
        return

    duration = total_frames / sample_rate
    try:
        recording = np.concatenate(chunks, axis=0)
        _write_wav(out_path, sample_rate, recording)
        size_kb = out_path.stat().st_size / 1024
        console.print(
            f"[bold green]✓ Đã lưu:[/bold green] {out_path.resolve()} "
            f"({size_kb:.1f} KB, {duration:.2f} giây)"
        )
    except OSError as exc:
        console.print(f"[red]Lỗi ghi tệp:[/red] {exc}")
    except Exception as exc:
        console.print(f"[red]Lỗi lưu WAV:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]", default="")


def _write_wav(path: Path, sample_rate: int, data) -> None:
    """Ghi WAV PCM 16-bit."""
    import wave
    import numpy as np

    arr = np.asarray(data)
    if arr.ndim == 1:
        channels = 1
    elif arr.ndim == 2:
        channels = arr.shape[1]
    else:
        raise ValueError("Dữ liệu ghi âm không hợp lệ.")
    if arr.dtype != np.int16:
        arr = np.clip(arr, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(arr.tobytes())
