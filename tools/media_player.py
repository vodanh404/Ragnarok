"""Trình phát nhạc Ragnarok chạy trực tiếp trong cùng cửa sổ CMD/Windows Terminal."""
from __future__ import annotations

import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rich.box import HEAVY
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ui.console import console
from ui.file_picker import choose_files

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".wma"}
REPEAT_MODES = ("tat", "mot", "tat_ca")


@dataclass
class Track:
    path: Path
    title: str
    artist: str = "Không rõ nghệ sĩ"
    album: str = "Không rõ album"
    duration: float = 0.0
    bitrate: int = 0

    @property
    def label(self) -> str:
        return f"{self.artist} — {self.title}"


def _safe_text(value: object, fallback: str) -> str:
    try:
        if isinstance(value, (list, tuple)):
            value = value[0] if value else fallback
        text = str(value).strip()
    except Exception:
        return fallback
    return text or fallback


def _number(value: object, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def _duration_with_ffprobe(path: Path) -> float:
    """Đọc thời lượng bằng ffprobe khi codec/container khó đọc bằng mutagen."""
    exe = shutil.which("ffprobe")
    if not exe:
        return 0.0
    try:
        result = subprocess.run(
            [
                exe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode == 0:
            return max(0.0, _number(result.stdout.strip()))
    except Exception:
        pass
    return 0.0


def _read_track(path: Path) -> Track:
    title = path.stem
    artist = "Không rõ nghệ sĩ"
    album = "Không rõ album"
    duration = 0.0
    bitrate = 0

    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(path, easy=False)
        if audio is not None:
            info = getattr(audio, "info", None)
            duration = _number(getattr(info, "length", 0.0))
            bitrate = int(_number(getattr(info, "bitrate", 0)))

            tags = getattr(audio, "tags", None)
            if tags:
                def read_tag(*keys: str, fallback: str) -> str:
                    for key in keys:
                        try:
                            value = tags.get(key)
                            if value is not None:
                                text = _safe_text(value, "")
                                if text:
                                    return text
                        except Exception:
                            continue
                    return fallback

                title = read_tag("TIT2", "title", "©nam", "©nam", fallback=title)
                artist = read_tag("TPE1", "artist", "©ART", fallback=artist)
                album = read_tag("TALB", "album", "©alb", fallback=album)
    except Exception:
        pass

    # Một số AAC/M4A/OGG/FLAC có thể không trả length ổn định.
    if duration <= 0:
        duration = _duration_with_ffprobe(path)

    # Dự phòng cuối: pygame đọc được thời lượng của một số định dạng mà mutagen không đọc được.
    if duration <= 0:
        try:
            import pygame
            sound = pygame.mixer.Sound(str(path))
            duration = max(0.0, float(sound.get_length()))
        except Exception:
            pass

    return Track(
        path=path,
        title=title,
        artist=artist,
        album=album,
        duration=duration,
        bitrate=bitrate,
    )


def _collect_audio(paths: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for p in paths:
        try:
            p = p.expanduser().resolve()
        except Exception:
            p = Path(p)
        candidates = p.rglob("*") if p.is_dir() else [p]
        for item in candidates:
            if not item.is_file() or item.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            key = str(item).casefold()
            if key not in seen:
                seen.add(key)
                out.append(item)
    return sorted(out, key=lambda x: (x.stem.casefold(), x.suffix.casefold()))


def _choose_folder(title: str = "Chọn thư mục nhạc") -> list[Path]:
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            folder = filedialog.askdirectory(title=title)
        finally:
            root.destroy()
        return [Path(folder)] if folder else []
    except Exception as exc:
        console.print(f"[yellow]Không mở được hộp chọn thư mục ({type(exc).__name__}).[/yellow]")
        raw = Prompt.ask("[bold]Đường dẫn thư mục[/bold]", default="").strip().strip('"')
        return [Path(raw)] if raw else []


def _format_time(seconds: float) -> str:
    if seconds <= 0:
        return "--:--"
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def _progress_bar(position: float, duration: float, width: int = 52) -> str:
    ratio = 0.0 if duration <= 0 else min(1.0, max(0.0, position / duration))
    filled = int(width * ratio)
    return "█" * filled + "░" * (width - filled)


class _Keyboard:
    def __enter__(self):
        self._old = None
        if sys.platform != "win32":
            import termios
            import tty
            self._old = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, exc_type, exc, tb):
        if sys.platform != "win32" and self._old is not None:
            import termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old)

    def get_key(self):
        if sys.platform == "win32":
            import msvcrt
            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                nxt = msvcrt.getwch()
                return {"K": "LEFT", "M": "RIGHT", "H": "UP", "P": "DOWN"}.get(nxt, nxt)
            if ch == "\r":
                return "ENTER"
            if ch == " ":
                return "SPACE"
            return ch.lower()

        import select
        if not select.select([sys.stdin], [], [], 0)[0]:
            return None
        ch = sys.stdin.read(1)
        if ch == " ":
            return "SPACE"
        if ch == "\x1b":
            if select.select([sys.stdin], [], [], 0.02)[0]:
                seq = sys.stdin.read(2)
                return {"[D": "LEFT", "[C": "RIGHT", "[A": "UP", "[B": "DOWN"}.get(seq, "ESC")
            return "ESC"
        return ch.lower()


class MusicPlayer:
    def __init__(self) -> None:
        self.tracks: list[Track] = []
        self.index = 0
        self.volume = 0.80
        self.repeat = "tat"
        self.shuffle = False
        self.paused = False
        self.base_position = 0.0
        self._pygame = None
        self._mixer_ready = False

    def init_audio(self) -> None:
        try:
            import pygame
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            self._pygame = pygame
            self._mixer_ready = True
        except Exception as exc:
            raise RuntimeError("Không khởi tạo được âm thanh. Hãy cài pygame và kiểm tra loa/tai nghe.") from exc

    def close(self) -> None:
        if self._mixer_ready and self._pygame:
            try:
                self._pygame.mixer.music.stop()
                self._pygame.mixer.quit()
            except Exception:
                pass
        self._mixer_ready = False

    @property
    def current(self) -> Track | None:
        return self.tracks[self.index] if self.tracks and 0 <= self.index < len(self.tracks) else None

    def load_tracks(self, paths: Iterable[Path], append: bool = False) -> int:
        files = _collect_audio(paths)
        if not append:
            self.tracks = []
            self.index = 0
        existing = {str(t.path).casefold() for t in self.tracks}
        added = 0
        for path in files:
            if str(path).casefold() not in existing:
                self.tracks.append(_read_track(path))
                existing.add(str(path).casefold())
                added += 1
        return added

    def play(self, index: int | None = None) -> None:
        if not self.tracks:
            return
        if index is not None:
            self.index = index % len(self.tracks)
        track = self.current
        if track is None:
            return
        self._pygame.mixer.music.load(str(track.path))
        self._pygame.mixer.music.set_volume(self.volume)
        self._pygame.mixer.music.play()
        self.paused = False
        self.base_position = 0.0

    def pause_toggle(self) -> None:
        if not self.current:
            return
        if self.paused:
            self._pygame.mixer.music.unpause()
            self.paused = False
        else:
            self.base_position = self.position()
            self._pygame.mixer.music.pause()
            self.paused = True

    def position(self) -> float:
        if not self.current or not self._mixer_ready:
            return 0.0
        if self.paused:
            return self.base_position
        pos_ms = self._pygame.mixer.music.get_pos()
        if pos_ms < 0:
            return self.base_position
        return self.base_position + pos_ms / 1000.0

    def seek(self, delta: float) -> None:
        track = self.current
        if not track:
            return
        current = self.position()
        limit = track.duration if track.duration > 0 else current + delta
        target = max(0.0, min(max(0.0, limit - 0.1), current + delta))
        try:
            self._pygame.mixer.music.play(start=target)
        except Exception:
            self._pygame.mixer.music.stop()
            self._pygame.mixer.music.load(str(track.path))
            self._pygame.mixer.music.play()
            try:
                self._pygame.mixer.music.set_pos(target)
            except Exception:
                pass
        self.base_position = target
        self.paused = False

    def volume_change(self, delta: float) -> None:
        self.volume = min(1.0, max(0.0, self.volume + delta))
        self._pygame.mixer.music.set_volume(self.volume)

    def next_track(self, auto: bool = False) -> None:
        if not self.tracks:
            return
        if self.repeat == "mot" and auto:
            self.play(self.index)
            return
        if self.shuffle and len(self.tracks) > 1:
            choices = [i for i in range(len(self.tracks)) if i != self.index]
            self.index = random.choice(choices)
        else:
            self.index += 1
            if self.index >= len(self.tracks):
                if self.repeat == "tat_ca":
                    self.index = 0
                else:
                    self.index = 0
                    self._pygame.mixer.music.stop()
                    self.base_position = 0.0
                    self.paused = False
                    return
        self.play(self.index)

    def previous_track(self) -> None:
        if not self.tracks:
            return
        if self.position() > 5:
            self.seek(-99999)
            return
        self.index = (self.index - 1) % len(self.tracks)
        self.play(self.index)

    def remove_current(self) -> None:
        if not self.tracks:
            return
        self._pygame.mixer.music.stop()
        del self.tracks[self.index]
        if self.tracks:
            self.index %= len(self.tracks)
            self.play(self.index)
        else:
            self.index = 0

    def maybe_advance(self) -> None:
        if not self.current or self.paused:
            return
        if not self._pygame.mixer.music.get_busy():
            self.next_track(auto=True)


def _render_player(player: MusicPlayer) -> Panel:
    track = player.current
    if track is None:
        return Panel("Chưa có bài hát. Nhấn [A] để thêm nhạc hoặc [F] để thêm thư mục.", title="[bold magenta]TRÌNH PHÁT NHẠC RAGNAROK[/bold magenta]", box=HEAVY)

    pos = min(track.duration, player.position()) if track.duration > 0 else player.position()
    if player.paused:
        status = "⏸ TẠM DỪNG"
    elif player._pygame.mixer.music.get_busy():
        status = "▶ ĐANG PHÁT"
    else:
        status = "■ ĐÃ DỪNG"

    repeat_text = {"tat": "Tắt", "mot": "Một bài", "tat_ca": "Tất cả"}[player.repeat]
    bitrate_text = f"{track.bitrate // 1000} kbps" if track.bitrate else "Không rõ"
    duration_text = _format_time(track.duration)
    position_text = _format_time(pos)

    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(justify="right", width=12)
    table.add_column(ratio=1)
    table.add_row("Bài", f"{player.index + 1}/{len(player.tracks)}")
    table.add_row("Tên", f"[bold white]{track.title}[/bold white]")
    table.add_row("Nghệ sĩ", track.artist)
    table.add_row("Album", track.album)
    table.add_row("Trạng thái", status)
    table.add_row("Tiến độ", f"[bold cyan]{_progress_bar(pos, track.duration)}[/bold cyan]")
    table.add_row("Thời gian", f"{position_text} / {duration_text}")
    table.add_row("Âm thanh", f"{track.path.suffix.upper().lstrip('.')} • {bitrate_text} • Âm lượng {round(player.volume * 100)}%")
    table.add_row("Chế độ", f"Ngẫu nhiên {'Bật' if player.shuffle else 'Tắt'} • Lặp {repeat_text}")
    table.add_row("Tệp", str(track.path))

    help_text = (
        "[Phím cách] Phát/Dừng  [N] Tiếp  [P] Trước  [←/→] Tua  [↑/↓] Âm lượng  "
        "[S] Ngẫu nhiên  [R] Lặp  [A] Thêm  [F] Thư mục  [L] Thư viện  [D] Xóa  [Q] Thoát"
    )
    return Panel(table, title="[bold magenta]TRÌNH PHÁT NHẠC RAGNAROK[/bold magenta]", subtitle=help_text, box=HEAVY)


def _render_library(player: MusicPlayer) -> None:
    console.clear()
    table = Table(title="[bold magenta]THƯ VIỆN NHẠC[/bold magenta]")
    table.add_column("#", justify="right", width=4)
    table.add_column("Tên bài", min_width=28)
    table.add_column("Nghệ sĩ", min_width=20)
    table.add_column("Album", min_width=20)
    table.add_column("Thời lượng", justify="right", width=10)
    for i, track in enumerate(player.tracks, 1):
        style = "bold cyan" if i - 1 == player.index else None
        table.add_row(str(i), track.title, track.artist, track.album, _format_time(track.duration), style=style)
    console.print(table)
    console.print("[dim]Nhập số bài để phát, hoặc để trống để quay lại.[/dim]")
    choice = Prompt.ask("Bài hát", default="").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(player.tracks):
            player.play(idx)


def _add_items(player: MusicPlayer) -> None:
    selected = choose_files(
        title="Chọn nhạc",
        filetypes=[("Tệp âm thanh", "*.mp3;*.wav;*.ogg;*.flac;*.m4a;*.aac;*.opus;*.wma"), ("Tất cả tệp", "*.*")],
        multiple=True,
        prompt="Thêm nhạc vào thư viện",
    )
    if selected:
        count = player.load_tracks(selected, append=True)
        console.print(f"[green]Đã thêm {count} tệp âm thanh.[/green]")
        time.sleep(0.6)


def _add_folder(player: MusicPlayer) -> None:
    folders = _choose_folder()
    if not folders:
        return
    count = player.load_tracks(folders, append=True)
    console.print(f"[green]Đã quét và thêm {count} tệp âm thanh.[/green]")
    time.sleep(0.6)


def feature_media_player() -> None:
    """Khởi chạy trình phát nhạc ngay trong cùng cửa sổ CMD/Windows Terminal."""
    player = MusicPlayer()
    try:
        player.init_audio()
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    console.clear()
    console.print(Panel(
        "1. Chọn nhiều tệp nhạc\n"
        "2. Chọn thư mục nhạc\n"
        "3. Nhập đường dẫn thư mục\n"
        "Q. Hủy",
        title="[bold magenta]MỞ TRÌNH PHÁT[/bold magenta]",
    ))
    mode = Prompt.ask("Lựa chọn", choices=["1", "2", "3", "q"], default="1")
    if mode == "q":
        player.close()
        return
    if mode == "1":
        selected = choose_files(
            title="Chọn nhạc",
            filetypes=[("Tệp âm thanh", "*.mp3;*.wav;*.ogg;*.flac;*.m4a;*.aac;*.opus;*.wma"), ("Tất cả tệp", "*.*")],
            multiple=True,
            prompt="Thêm nhạc",
        )
    elif mode == "2":
        selected = _choose_folder()
    else:
        raw = Prompt.ask("Đường dẫn thư mục", default="").strip().strip('"')
        selected = [Path(raw)] if raw else []

    if selected:
        player.load_tracks(selected, append=False)
    if not player.tracks:
        console.print("[yellow]Không tìm thấy tệp nhạc được hỗ trợ.[/yellow]")
        player.close()
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    try:
        player.play(0)
    except Exception as exc:
        player.close()
        console.print(f"[red]Không phát được bài đầu tiên: {exc}[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    try:
        # Màn hình Live tạm thời; khi thoát Rich sẽ tự xóa bản render cuối.
        with _Keyboard() as keyboard:
            with Live(_render_player(player), console=console, refresh_per_second=8, screen=False, transient=True) as live:
                while True:
                    key = keyboard.get_key()
                    if key is not None:
                        if key in ("q", "ESC"):
                            break
                        if key == "SPACE":
                            player.pause_toggle()
                        elif key == "n":
                            player.next_track()
                        elif key == "p":
                            player.previous_track()
                        elif key == "LEFT":
                            player.seek(-5)
                        elif key == "RIGHT":
                            player.seek(5)
                        elif key == "UP":
                            player.volume_change(0.05)
                        elif key == "DOWN":
                            player.volume_change(-0.05)
                        elif key == "s":
                            player.shuffle = not player.shuffle
                        elif key == "r":
                            player.repeat = REPEAT_MODES[(REPEAT_MODES.index(player.repeat) + 1) % len(REPEAT_MODES)]
                        elif key == "d":
                            player.remove_current()
                        elif key == "a":
                            live.stop(); _add_items(player)
                            live.start(refresh=True)
                        elif key == "f":
                            live.stop(); _add_folder(player)
                            live.start(refresh=True)
                        elif key == "l":
                            live.stop(); _render_library(player)
                            live.start(refresh=True)
                        live.update(_render_player(player), refresh=True)

                    player.maybe_advance()
                    live.update(_render_player(player), refresh=True)
                    time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        player.close()
        console.clear()
        console.print("\n[green]Đã thoát trình phát nhạc.[/green]")
        time.sleep(0.4)
