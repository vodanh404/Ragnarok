"""
Rút gọn URL / giải mã link rút gọn (port ý tưởng từ qxresearch Link Shortener).
Dùng is.gd / tinyurl qua HTTP – không bắt buộc pyshorteners.
"""

from urllib.parse import urlparse

from rich.panel import Panel
from rich.prompt import Prompt

from ui.console import console


def _is_plausible_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _shorten_isgd(url: str) -> str:
    import requests

    resp = requests.get(
        "https://is.gd/create.php",
        params={"format": "simple", "url": url},
        timeout=15,
    )
    resp.raise_for_status()
    text = resp.text.strip()
    if text.startswith("Error:") or not text.startswith("http"):
        raise RuntimeError(text or "is.gd trả về kết quả không hợp lệ")
    return text


def _shorten_tinyurl(url: str) -> str:
    import requests

    resp = requests.get(
        "https://tinyurl.com/api-create.php",
        params={"url": url},
        timeout=15,
    )
    resp.raise_for_status()
    text = resp.text.strip()
    if not text.startswith("http"):
        raise RuntimeError(text or "TinyURL trả về kết quả không hợp lệ")
    return text


def _expand_url(url: str) -> str:
    """Theo dõi redirect để lấy URL gốc (HEAD rồi GET nếu cần)."""
    import requests

    resp = requests.head(url, allow_redirects=True, timeout=15)
    if resp.url and resp.url != url:
        return resp.url
    # Một số shortener không trả Location trên HEAD
    resp = requests.get(url, allow_redirects=True, timeout=15, stream=True)
    resp.close()
    return resp.url or url


def feature_link_tool() -> None:
    """Rút gọn URL hoặc giải mã link rút gọn."""
    console.print("[bold cyan]═══ RÚT GỌN / GIẢI MÃ URL ═══[/bold cyan]\n")
    console.print(
        "[dim]1 = Rút gọn URL  |  2 = Giải mã (expand) link rút gọn[/dim]\n"
    )

    mode = Prompt.ask("[bold]Chế độ[/bold]", choices=["1", "2"], default="1")
    url = Prompt.ask("[bold]Nhập URL[/bold]").strip()
    if not url:
        console.print("[red]URL trống. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return
    if not _is_plausible_url(url):
        console.print("[red]URL không hợp lệ (cần http:// hoặc https://).[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    try:
        import requests  # noqa: F401
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] [yellow]pip install requests[/yellow]"
        )
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    try:
        if mode == "1":
            try:
                short = _shorten_isgd(url)
            except Exception:
                console.print("[yellow]is.gd lỗi, thử TinyURL...[/yellow]")
                short = _shorten_tinyurl(url)
            console.print(
                Panel(
                    f"[bold]Gốc:[/bold]  {url}\n[bold green]Rút gọn:[/bold green] {short}",
                    title="Kết quả",
                    border_style="green",
                )
            )
        else:
            real = _expand_url(url)
            console.print(
                Panel(
                    f"[bold]Rút gọn:[/bold] {url}\n[bold green]Gốc:[/bold green]    {real}",
                    title="Kết quả",
                    border_style="green",
                )
            )
    except requests.exceptions.Timeout:
        console.print("[red]Hết thời gian chờ (timeout). Kiểm tra mạng.[/red]")
    except requests.exceptions.ConnectionError:
        console.print("[red]Lỗi mạng – kiểm tra kết nối Internet.[/red]")
    except Exception as exc:
        console.print(f"[red]Lỗi:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_link_tool
