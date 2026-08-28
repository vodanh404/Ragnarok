"""
AI Chat CLI (port terminal chat từ module_AI/Chat_bot.py).
Yêu cầu: google-genai + API key Gemini.
"""

import configparser
import os
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Prompt

from ui.console import console

APP_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = APP_ROOT / "config.ini"

# Model Flash ổn định hiện hành (gemini-2.0-flash đã shutdown 01/06/2026)
DEFAULT_MODEL = "gemini-3.6-flash"


def _load_gemini_api_key() -> str:
    """Đọc API key từ env rồi config.ini. Không hard-code."""
    key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or ""
    ).strip()
    if key:
        return key

    if CONFIG_FILE.exists():
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding="utf-8")
        if config.has_section("Gemini"):
            return config.get("Gemini", "API_Key", fallback="").strip()
        if config.has_section("Settings"):
            # Tương thích nếu người dùng lưu chung section
            return config.get("Settings", "Gemini_API_Key", fallback="").strip()
    return ""


def _save_gemini_api_key(api_key: str) -> None:
    """Lưu API key vào config.ini (section Gemini)."""
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")
    if not config.has_section("Gemini"):
        config.add_section("Gemini")
    config.set("Gemini", "API_Key", api_key)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        config.write(f)


def _friendly_api_error(exc: Exception) -> str:
    """Chuyển exception kỹ thuật thành thông báo thân thiện."""
    msg = str(exc).lower()
    name = type(exc).__name__.lower()

    if "api_key" in msg or "authentication" in msg or "401" in msg or "permission" in msg:
        return (
            "Lỗi xác thực API key. Kiểm tra lại GEMINI_API_KEY / GOOGLE_API_KEY "
            "hoặc key trong config.ini."
        )
    if "quota" in msg or "rate" in msg or "429" in msg or "resource_exhausted" in msg:
        return "Đã hết hạn mức (quota) hoặc bị giới hạn tốc độ. Thử lại sau."
    if "not found" in msg or "404" in msg or "model" in msg and "not" in msg:
        return (
            f"Model không tồn tại hoặc đã bị tắt. "
            f"Thử model khác (ví dụ: {DEFAULT_MODEL})."
        )
    if "timeout" in msg or "timed out" in msg or "deadline" in msg:
        return "Hết thời gian chờ (timeout). Kiểm tra mạng và thử lại."
    if "connection" in msg or "network" in msg or "unreachable" in msg:
        return "Lỗi kết nối mạng. Kiểm tra Internet."
    if "invalid" in msg and "key" in msg:
        return "API key không hợp lệ."
    return f"Lỗi API ({type(exc).__name__}): {exc}"


def feature_ai_waifu() -> None:
    """Chat đơn giản với Gemini (CLI)."""
    console.print("[bold cyan]═══ AI CHAT / WAIFU (Gemini) ═══[/bold cyan]\n")
    console.print(
        "[dim]Phiên bản CLI. Live2D GUI cần Tkinter + live2d + pygame "
        "(xem module gốc module_AI/AI_Waifu.py).[/dim]\n"
    )

    api_key = _load_gemini_api_key()
    if api_key:
        console.print("[green]Đã tìm thấy API key (env hoặc config.ini).[/green]")
        use_saved = Prompt.ask(
            "Dùng key đã có?", choices=["y", "n"], default="y"
        )
        if use_saved == "n":
            api_key = Prompt.ask(
                "[bold]Gemini API key[/bold]",
                password=True,
            ).strip()
    else:
        console.print(
            "[dim]Có thể set env GEMINI_API_KEY / GOOGLE_API_KEY "
            "hoặc lưu vào config.ini [Gemini] API_Key.[/dim]"
        )
        api_key = Prompt.ask(
            "[bold]Gemini API key[/bold] (hoặc set env GEMINI_API_KEY)",
            password=True,
        ).strip()

    if not api_key:
        console.print("[red]Thiếu API key. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    # Lưu nếu người dùng muốn (chỉ khi vừa nhập mới)
    save = Prompt.ask(
        "Lưu API key vào config.ini?", choices=["y", "n"], default="n"
    )
    if save == "y":
        try:
            _save_gemini_api_key(api_key)
            console.print("[green]Đã lưu API key vào config.ini[/green]")
        except OSError as exc:
            console.print(f"[yellow]Không lưu được config.ini:[/yellow] {exc}")

    try:
        from google import genai
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] "
            "[yellow]pip install google-genai[/yellow]"
        )
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    model = Prompt.ask(
        "[bold]Model[/bold]",
        default=DEFAULT_MODEL,
    ).strip() or DEFAULT_MODEL

    try:
        client = genai.Client(api_key=api_key)
        chat = client.chats.create(model=model)
    except Exception as exc:
        console.print(f"[red]Không khởi tạo được chat:[/red] {_friendly_api_error(exc)}")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    console.print(
        Panel(
            f"Model: [yellow]{model}[/yellow]\n"
            "Gõ tin nhắn để chat. [cyan]/exit[/cyan] hoặc [cyan]q[/cyan] để thoát.",
            title="AI Chat sẵn sàng",
            border_style="magenta",
        )
    )

    while True:
        user_msg = Prompt.ask("[bold green]Bạn[/bold green]").strip()
        if not user_msg or user_msg.lower() in ("q", "quit", "exit", "/exit"):
            break
        try:
            response = chat.send_message(user_msg)
            text = getattr(response, "text", None) or str(response)
            console.print(f"[bold magenta]AI[/bold magenta]: {text}\n")
        except Exception as exc:
            console.print(f"[red]Lỗi gửi tin:[/red] {_friendly_api_error(exc)}\n")

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_ai_waifu
