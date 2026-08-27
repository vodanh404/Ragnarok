"""
Tìm kiếm Wikipedia (port từ modules/wiki_search.py).
"""

from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from ui.console import console


def feature_wiki() -> None:
    """Tóm tắt bài viết Wikipedia (tiếng Việt)."""
    console.print("[bold cyan]═══ TÌM KIẾM WIKIPEDIA ═══[/bold cyan]\n")

    try:
        import wikipedia
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install wikipedia[/yellow]"
        )
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    wikipedia.set_lang("vi")
    query = Prompt.ask("[bold]Từ khóa tìm kiếm[/bold]").strip()
    if not query:
        console.print("[red]Từ khóa trống.[/red]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
        return

    try:
        summary = wikipedia.summary(query, sentences=8)
        console.print(Panel(Markdown(summary), title=query, border_style="green"))
    except wikipedia.exceptions.PageError:
        console.print(f"[red]Không tìm thấy trang về '{query}'.[/red]")
    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:8])
        console.print(
            f"[yellow]'{query}' có nhiều nghĩa.[/yellow]\n"
            f"Gợi ý: {options}..."
        )
    except Exception as exc:
        console.print(f"[red]Lỗi:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]")
