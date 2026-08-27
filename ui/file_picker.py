"""Native file dialogs with CLI fallback for Ragnarok Control Center."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from rich.prompt import Prompt

from ui.console import console


def _dialog_pick(*, multiple: bool, filetypes: Iterable[tuple[str, str]], title: str):
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            if multiple:
                return list(
                    filedialog.askopenfilenames(
                        title=title,
                        filetypes=list(filetypes),
                    )
                )
            chosen = filedialog.askopenfilename(
                title=title,
                filetypes=list(filetypes),
            )
            return [chosen] if chosen else []
        finally:
            root.destroy()
    except Exception as exc:
        console.print(
            f"[yellow]Không mở được hộp thoại chọn tệp ({type(exc).__name__}). "
            "Chuyển sang nhập đường dẫn.[/yellow]"
        )
        return None


def choose_files(
    *,
    title: str,
    filetypes: Iterable[tuple[str, str]],
    multiple: bool = False,
    prompt: str = "Chọn cách nhập file",
) -> list[Path]:
    """Offer native file picker or manual path entry. Returns existing files only."""
    mode = Prompt.ask(
        f"[bold]{prompt}[/bold]",
        choices=["1", "2", "q"],
        default="1",
    )
    if mode == "q":
        return []

    if mode == "1":
        selected = _dialog_pick(
            multiple=multiple,
            filetypes=filetypes,
            title=title,
        )
        if selected is not None:
            paths = [Path(p) for p in selected if p]
            missing = [p for p in paths if not p.is_file()]
            if missing:
                console.print("[red]Một số tệp không còn tồn tại:[/red]")
                for p in missing:
                    console.print(f"  • {p}")
            return [p for p in paths if p.is_file()]
        # dialog unavailable -> continue to manual mode

    if multiple:
        console.print(
            "[dim]Nhập từng đường dẫn, để trống để kết thúc. Bạn cũng có thể "
            "dán nhiều đường dẫn cách nhau bằng dấu phẩy.[/dim]"
        )
        paths: list[Path] = []
        while True:
            raw = Prompt.ask(f"[bold]Tệp số #{len(paths) + 1}[/bold] (để trống = hoàn tất)", default="").strip()
            if not raw:
                break
            for item in raw.split(","):
                item = item.strip().strip('"')
                if not item:
                    continue
                p = Path(item).expanduser()
                if p.is_file():
                    paths.append(p)
                else:
                    console.print(f"[red]Không tìm thấy tệp:[/red] {p}")
        return paths

    raw = Prompt.ask("[bold]Đường dẫn file[/bold]").strip().strip('"')
    if not raw:
        return []
    path = Path(raw).expanduser()
    if not path.is_file():
        console.print(f"[red]Không tìm thấy tệp:[/red] {path}")
        return []
    return [path]
