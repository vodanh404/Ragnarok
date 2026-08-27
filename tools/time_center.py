"""Trung tâm thời gian: đồng hồ, lịch, đếm ngược và đồng hồ cà chua."""
from __future__ import annotations

import calendar
import time
from datetime import datetime

from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ui.console import console
from ui.header import clear_screen

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
MONTHS = ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
          "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]


def duration_text(seconds: float) -> str:
    total = max(0, int(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def clock_panel(now: datetime) -> Panel:
    body = Group(
        Align.center(Text(now.strftime("%H:%M:%S"), style="bold cyan")),
        Align.center(Text(f"{DAYS[now.weekday()]}, ngày {now.day:02d}/{now.month:02d}/{now.year}", style="bold white")),
        Align.center(Text(now.strftime("Múi giờ: %Z").strip() or "Múi giờ hệ thống", style="dim")),
    )
    return Panel(body, title="ĐỒNG HỒ HIỆN TẠI", border_style="cyan", padding=(1, 5))


def show_clock() -> None:
    clear_screen()
    console.print("[dim]Nhấn Ctrl+C để dừng đồng hồ.[/dim]\n")
    try:
        with Live(clock_panel(datetime.now()), refresh_per_second=4, console=console, transient=True) as live:
            while True:
                live.update(clock_panel(datetime.now()), refresh=True)
                time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        clear_screen()


def calendar_table(year: int, month: int) -> Table:
    table = Table(title=f"{MONTHS[month - 1]} {year}", border_style="cyan", expand=False)
    for day in DAYS:
        table.add_column(day, justify="center", width=10)
    today = datetime.now().date()
    for week in calendar.monthcalendar(year, month):
        cells = []
        for column, day in enumerate(week):
            if not day:
                cells.append(" ")
            elif year == today.year and month == today.month and day == today.day:
                cells.append(f"[bold cyan]◆ {day:02d}[/bold cyan]")
            elif column >= 5:
                cells.append(f"[yellow]{day:02d}[/yellow]")
            else:
                cells.append(f"{day:02d}")
        table.add_row(*cells)
    return table


def _move_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    if index < 12 or index > 9999 * 12 + 11:
        return year, month
    view_year, view_month = divmod(index, 12)
    return view_year, view_month + 1


def show_calendar() -> None:
    now = datetime.now()
    try:
        year = int(Prompt.ask("Năm", default=str(now.year)))
        month = int(Prompt.ask("Tháng (1-12)", default=str(now.month)))
        if not 1 <= year <= 9999 or not 1 <= month <= 12:
            raise ValueError
    except ValueError:
        console.print("[red]Tháng hoặc năm không hợp lệ.[/red]")
        return

    while True:
        clear_screen()
        console.print(Panel("[bold red]RAGNAROK • LỊCH[/bold red]", border_style="red"))
        console.print(calendar_table(year, month))
        console.print("\n[dim]← tháng trước   → tháng sau   q: quay lại[/dim]")
        key = Prompt.ask("Lựa chọn", choices=["p", "t", "q"], default="q")
        if key == "q":
            return
        year, month = _move_month(year, month, -1 if key == "p" else 1)


def ask_duration() -> int:
    raw = Prompt.ask("Thời lượng (GIỜ:PHÚT:GIÂY hoặc số giây)", default="00:05:00").strip()
    if raw.isdigit():
        seconds = int(raw)
    else:
        parts = raw.split(":")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise ValueError
        hours, minutes, secs = map(int, parts)
        if minutes >= 60 or secs >= 60:
            raise ValueError
        seconds = hours * 3600 + minutes * 60 + secs
    if seconds <= 0 or seconds > 99 * 3600 + 59 * 60 + 59:
        raise ValueError
    return seconds


def _run_timer(total: int, title: str, completion: str) -> None:
    finish = time.monotonic() + total
    with Progress(TextColumn(f"[bold cyan]{title}[/bold cyan]"), BarColumn(bar_width=42),
                  TextColumn("{task.percentage:>6.1f}%"), TextColumn("• còn {task.fields[remaining]}"),
                  console=console, transient=True) as progress:
        task = progress.add_task("", total=total, remaining=duration_text(total))
        try:
            while True:
                remaining = max(0.0, finish - time.monotonic())
                progress.update(task, completed=total - remaining, remaining=duration_text(remaining))
                if remaining <= 0:
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            raise
    console.print(Panel(f"[bold green]{duration_text(0)}[/bold green]\n\n🔔 {completion}", title="HOÀN TẤT", border_style="green"))
    print("\a", end="", flush=True)


def show_countdown() -> None:
    try:
        total = ask_duration()
    except ValueError:
        console.print("[red]Thời lượng không hợp lệ.[/red]")
        return
    try:
        _run_timer(total, "ĐẾM NGƯỢC", "Đã hết thời gian!")
    except KeyboardInterrupt:
        console.print("\n[yellow]Đã hủy đếm ngược.[/yellow]")


def show_pomodoro() -> None:
    try:
        work = int(Prompt.ask("Thời gian tập trung (phút)", default="25"))
        short = int(Prompt.ask("Nghỉ ngắn (phút)", default="5"))
        long = int(Prompt.ask("Nghỉ dài (phút)", default="15"))
        cycles = int(Prompt.ask("Số vòng", default="4"))
        if min(work, short, long, cycles) <= 0 or cycles > 99:
            raise ValueError
    except ValueError:
        console.print("[red]Thiết lập không hợp lệ.[/red]")
        return

    phases = []
    for number in range(1, cycles + 1):
        phases.append((f"TẬP TRUNG • Vòng {number}/{cycles}", work * 60))
        if number < cycles:
            phases.append(("NGHỈ NGẮN", short * 60))
    phases.append(("NGHỈ DÀI • Hoàn thành", long * 60))

    try:
        for title, seconds in phases:
            clear_screen()
            _run_timer(seconds, title, f"{title} đã hoàn tất!")
        console.print(Panel("[bold cyan]Bạn đã hoàn thành phiên tập trung.[/bold cyan]",
                            title="ĐỒNG HỒ CÀ CHUA", border_style="cyan"))
    except KeyboardInterrupt:
        console.print("\n[yellow]Đã dừng đồng hồ cà chua.[/yellow]")


def feature_time_center(mode: str | None = None) -> None:
    if mode == "1":
        show_clock()
    elif mode == "2":
        show_calendar()
    elif mode == "3":
        show_countdown()
    elif mode == "4":
        show_pomodoro()
