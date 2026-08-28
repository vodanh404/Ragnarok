"""System monitor: CPU, RAM, disks, network, battery and optional NVIDIA GPU."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.live import Live
from rich.prompt import Confirm, Prompt

from ui.console import console


def _psutil():
    try:
        import psutil
        return psutil
    except ImportError:
        console.print("[yellow]Thiếu psutil. Hãy chạy: pip install psutil[/yellow]")
        return None


def _gpu_info():
    """Read NVIDIA GPU info without requiring a Python NVIDIA package."""
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if p.returncode != 0:
            return []
        rows = []
        for line in p.stdout.strip().splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) >= 6:
                rows.append(parts)
        return rows
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return []


def _bytes(n: int | float) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _snapshot(ps):
    disks = []
    for part in ps.disk_partitions(all=False):
        try:
            u = ps.disk_usage(part.mountpoint)
            disks.append((part.mountpoint, u.percent, _bytes(u.used), _bytes(u.total)))
        except (PermissionError, OSError):
            continue
    net = ps.net_io_counters()
    battery = ps.sensors_battery()
    return {
        "cpu": ps.cpu_percent(interval=0.4),
        "cores": ps.cpu_count(logical=False) or 0,
        "threads": ps.cpu_count(logical=True) or 0,
        "ram": ps.virtual_memory(),
        "swap": ps.swap_memory(),
        "disk": disks,
        "net": net,
        "battery": battery,
        "boot": ps.boot_time(),
        "gpu": _gpu_info(),
    }


def _render(s, live=False):
    table = Table(title="🖥️ SYSTEM MONITOR", border_style="red", header_style="bold yellow")
    table.add_column("Chỉ số", style="bold white")
    table.add_column("Giá trị", style="cyan")
    table.add_row("Hệ điều hành", f"{platform.system()} {platform.release()} ({platform.machine()})")
    table.add_row("CPU", f"{s['cpu']:.1f}%  | {s['cores']} cores / {s['threads']} threads")
    table.add_row("RAM", f"{_bytes(s['ram'].used)} / {_bytes(s['ram'].total)}  ({s['ram'].percent:.1f}%)")
    table.add_row("Swap", f"{_bytes(s['swap'].used)} / {_bytes(s['swap'].total)}  ({s['swap'].percent:.1f}%)")
    for mount, pct, used, total in s["disk"][:8]:
        table.add_row(f"Disk {mount}", f"{used} / {total}  ({pct:.1f}%)")
    if s["battery"]:
        state = "AC" if s["battery"].power_plugged else "Battery"
        table.add_row("Pin", f"{s['battery'].percent:.0f}%  ({state})")
    if s["gpu"]:
        for i, g in enumerate(s["gpu"]):
            table.add_row(f"GPU {i}", f"{g[0]} | {g[2]}% | {g[3]}/{g[4]} MB | {g[1]}°C | {g[5]} W")
    else:
        table.add_row("GPU", "Không phát hiện NVIDIA nvidia-smi")
    table.add_row("Network", f"↑ {_bytes(s['net'].bytes_sent)}  ↓ {_bytes(s['net'].bytes_recv)}")
    return table


def _poll_key() -> str:
    """Non-blocking key polling for Live Monitor on Windows/POSIX."""
    import os
    if os.name == "nt":
        try:
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getwch().lower()
        except Exception:
            return ""
        return ""
    try:
        import select, sys, termios, tty
        if not sys.stdin.isatty():
            return ""
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if not ready:
            return ""
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        return ""


def feature_system_monitor() -> None:
    ps = _psutil()
    if not ps:
        Prompt.ask("Enter để quay lại")
        return
    while True:
        show = _snapshot(ps)
        console.print(_render(show))
        console.print("[dim]R = refresh | L = live monitor | 0 = quay lại[/dim]")
        choice = Prompt.ask("[bold red]Lựa chọn[/bold red]", choices=["r", "l", "0"], default="r").lower()
        if choice == "0":
            return
        if choice == "l":
            console.print("[dim]Live Monitor: nhấn [bold]Q[/bold] hoặc [bold]0[/bold] để thoát; Ctrl+C cũng được.[/dim]")
            try:
                with Live(_render(_snapshot(ps)), refresh_per_second=2, screen=False) as live:
                    while True:
                        time.sleep(0.5)
                        # Không dùng input() trong Live vì nó làm treo giao diện.
                        key = _poll_key()
                        if key in {"q", "0", "\x1b"}:
                            break
                        live.update(_render(_snapshot(ps)))
            except KeyboardInterrupt:
                pass
        console.print()

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_system_monitor
