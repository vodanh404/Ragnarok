"""
Tra cứu thời tiết OpenWeatherMap (port từ modules/weather.py).
"""

import configparser
import os
import time
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Prompt

from ui.console import console

APP_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = APP_ROOT / "config.ini"


def _load_api_key() -> str:
    """Ưu tiên env OPENWEATHER_API_KEY / OPENWEATHERMAP_API_KEY, rồi config.ini."""
    key = (
        os.environ.get("OPENWEATHER_API_KEY")
        or os.environ.get("OPENWEATHERMAP_API_KEY")
        or ""
    ).strip()
    if key:
        return key

    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")
        return config.get("Settings", "API_Key", fallback="").strip()
    return ""


def _save_api_key(api_key: str) -> None:
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")
    if not config.has_section("Settings"):
        config.add_section("Settings")
    config.set("Settings", "API_Key", api_key)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        config.write(f)


def feature_weather() -> None:
    """Tra cứu thời tiết theo thành phố."""
    console.print("[bold cyan]═══ TRA CỨU THỜI TIẾT ═══[/bold cyan]\n")
    console.print("[dim]API: openweathermap.org (cần API key miễn phí)[/dim]\n")
    console.print(
        "[dim]Cấu hình: env OPENWEATHER_API_KEY hoặc config.ini [Settings] API_Key[/dim]\n"
    )

    api_key = _load_api_key()
    if api_key:
        console.print("[green]Đã có API key (env hoặc config.ini)[/green]")
        use_saved = Prompt.ask(
            "Dùng key đã có?", choices=["y", "n"], default="y"
        )
        if use_saved == "n":
            api_key = Prompt.ask("[bold]Nhập API key mới[/bold]").strip()
    else:
        console.print(
            "[yellow]Chưa có API key.[/yellow]\n"
            "Cách cấu hình:\n"
            "  1. Set env: [cyan]export OPENWEATHER_API_KEY=your_key[/cyan]\n"
            "  2. Hoặc nhập key bên dưới (sẽ lưu vào config.ini)\n"
            "  3. Lấy key miễn phí tại: https://openweathermap.org/api\n"
        )
        api_key = Prompt.ask("[bold]Nhập OpenWeatherMap API key[/bold]").strip()

    if not api_key:
        console.print(
            "[red]Thiếu API key. Hủy.[/red]\n"
            "[dim]Set OPENWEATHER_API_KEY hoặc thêm vào config.ini.[/dim]"
        )
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    # Chỉ lưu khi người dùng vừa nhập (không ghi đè nếu lấy từ env)
    if not (
        os.environ.get("OPENWEATHER_API_KEY")
        or os.environ.get("OPENWEATHERMAP_API_KEY")
    ):
        try:
            _save_api_key(api_key)
        except OSError as exc:
            console.print(f"[yellow]Không lưu được config.ini:[/yellow] {exc}")

    city = Prompt.ask("[bold]Tên thành phố[/bold]", default="Ho Chi Minh").strip()
    if not city:
        console.print("[red]Tên thành phố trống.[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    try:
        import requests
        from unidecode import unidecode
    except ImportError:
        console.print(
            "[red]Thiếu thư viện. Cài đặt:[/red] "
            "[yellow]pip install requests unidecode[/yellow]"
        )
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    city_norm = unidecode(city)
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?appid={api_key}&q={city_norm}&units=metric&lang=vi"
    )

    try:
        resp = None
        last_error = None
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code >= 500 and attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                break
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
                else:
                    raise
        if resp is None:
            raise last_error or RuntimeError("Không nhận được phản hồi từ máy chủ.")
        data = resp.json()

        # OpenWeatherMap trả cod dạng int hoặc str
        cod = data.get("cod")
        if str(cod) == "200":
            info = (
                f"[bold]{data['name']}, {data['sys'].get('country', '')}[/bold]\n\n"
                f"🌡️  Nhiệt độ : [yellow]{data['main']['temp']}°C[/yellow]\n"
                f"   Cảm giác : {data['main'].get('feels_like', 'N/A')}°C\n"
                f"🌬️  Áp suất  : {data['main']['pressure']} hPa\n"
                f"💦  Độ ẩm   : {data['main']['humidity']}%\n"
                f"☁️  Thời tiết: {data['weather'][0]['description'].capitalize()}\n"
                f"💨  Gió     : {data.get('wind', {}).get('speed', 'N/A')} m/s"
            )
            console.print(Panel(info, title="Kết quả", border_style="green"))
        else:
            message = data.get("message", data)
            if str(cod) == "401":
                console.print(
                    "[red]API key không hợp lệ hoặc chưa kích hoạt.[/red]\n"
                    "[dim]Kiểm tra key trên openweathermap.org (có thể mất vài giờ sau khi tạo).[/dim]"
                )
            elif str(cod) == "404":
                console.print(f"[red]Không tìm thấy thành phố:[/red] {city}")
            else:
                console.print(
                    f"[red]Lỗi API ({cod}):[/red] {message}"
                )
    except requests.exceptions.Timeout:
        console.print("[red]Hết thời gian chờ (timeout). Thử lại sau.[/red]")
    except requests.exceptions.ConnectionError:
        console.print("[red]Lỗi mạng – kiểm tra kết nối Internet.[/red]")
    except requests.exceptions.RequestException as exc:
        console.print(f"[red]Lỗi HTTP:[/red] {exc}")
    except (KeyError, TypeError, ValueError) as exc:
        console.print(f"[red]Phản hồi API không đúng định dạng:[/red] {exc}")
    except Exception as exc:
        console.print(f"[red]Lỗi:[/red] {exc}")

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")

# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_weather
