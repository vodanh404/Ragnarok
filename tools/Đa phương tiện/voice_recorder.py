"""Microphone recorder with free start/stop timing.

Recording begins only after the user presses Enter and continues until Enter is
pressed again. The stream runs in the background while Rich waits for the stop
command, so there is no fixed duration.
"""

from datetime import datetime
from pathlib import Path

from rich.prompt import Prompt

from ui.console import console
from output_paths import output_path

MAX_RECORD_SECONDS = 3600


def feature_voice_recorder() -> None:
    """Record microphone audio until the user presses Enter to stop."""
    console.print("[bold cyan]═══ GHI ÂM (VOICE RECORDER) ═══[/bold cyan]\n")

    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red]\n"
            "[yellow]pip install sounddevice numpy[/yellow]\n"
            "[dim]Trên Linux có thể cần: sudo apt install libportaudio2[/dim]"
        )
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    sample_rate_raw = Prompt.ask(
        "[bold]Sample rate[/bold]",
        default="44100",
    ).strip() or "44100"
    try:
        sample_rate = int(sample_rate_raw)
        if not 8000 <= sample_rate <= 192000:
            raise ValueError
    except ValueError:
        console.print("[yellow]Sample rate không hợp lệ, dùng 44100 Hz.[/yellow]")
        sample_rate = 44100

    default_name = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.wav"
    name = Prompt.ask(
        "[bold]Tên file[/bold]",
        default=default_name,
    ).strip() or default_name
    if not name.lower().endswith(".wav"):
        name += ".wav"
    out_path = output_path("recordings", name, default_name)
    if out_path.exists():
        from rich.prompt import Confirm
        if not Confirm.ask(f"[yellow]File đã tồn tại:[/yellow] {out_path}. Ghi đè?", default=False):
            console.print("[dim]Đã hủy để tránh ghi đè file.[/dim]")
            Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
            return

    channels = 1
    console.print("[dim]Nhấn Enter để BẮT ĐẦU ghi âm.[/dim]")
    Prompt.ask("", default="")
    console.print("[bold green]● ĐANG GHI ÂM[/bold green] — nhấn Enter để DỪNG.")
    console.print(f"[dim]Giới hạn an toàn: {MAX_RECORD_SECONDS // 60} phút.[/dim]")

    chunks = []
    total_frames = 0
    started = False

    def callback(indata, frames, _time, status):
        nonlocal total_frames
        if status:
            console.print(f"[yellow]Audio status:[/yellow] {status}")
        # Copy because sounddevice reuses the callback buffer.
        chunks.append(indata.copy())
        total_frames += frames

    stream = None
    try:
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="int16",
            callback=callback,
            blocksize=0,
        )
        stream.start()
        started = True
        Prompt.ask("", default="")
    except KeyboardInterrupt:
        console.print("\n[yellow]Đã dừng ghi âm bằng Ctrl+C.[/yellow]")
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

    if not started or total_frames <= 0 or not chunks:
        console.print("[yellow]Không có dữ liệu âm thanh để lưu.[/yellow]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    duration = total_frames / sample_rate
    if duration > MAX_RECORD_SECONDS:
        console.print("[yellow]Bản ghi vượt giới hạn an toàn; dữ liệu sẽ được lưu phần đã thu được.[/yellow]")

    try:
        recording = np.concatenate(chunks, axis=0)
        _write_wav(out_path, sample_rate, recording)
        size_kb = out_path.stat().st_size / 1024
        console.print(
            f"[bold green]✓ Đã lưu:[/bold green] {out_path.resolve()} "
            f"({size_kb:.1f} KB, {duration:.2f} giây)"
        )
    except OSError as exc:
        console.print(f"[red]Lỗi ghi file:[/red] {exc}")
    except Exception as exc:
        console.print(f"[red]Lỗi lưu WAV:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")


def _write_wav(path: Path, sample_rate: int, data) -> None:
    """Ghi WAV PCM 16-bit mono/stereo từ numpy array."""
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

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_voice_recorder
