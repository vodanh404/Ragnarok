"""Hệ thống menu chính của RAGNAROK."""

from typing import Callable

from rich.prompt import Prompt
from rich.table import Table

from ui.header import show_header
from ui.console import console
from tools import (
    feature_camera, feature_qr_scan, feature_qr, feature_barcode, feature_weather,
    feature_pokemon, feature_element, feature_ai_waifu, feature_tts, feature_downloader,
    feature_password, feature_wiki, feature_media_player, feature_link_tool,
    feature_pdf_merge, feature_pdf_protect, feature_audio_extract, feature_screenshot,
    feature_voice_recorder, feature_audiobook, feature_system_monitor,
    feature_terminal_image, feature_time_center,
)


def _open_feature(feature: Callable[[], None]) -> None:
    """Mở một chức năng trên màn hình riêng, luôn dọn sạch khi vào/ra."""
    from ui.header import clear_screen
    clear_screen()
    show_header()
    try:
        feature()
    except KeyboardInterrupt:
        console.print("\n[yellow]Đã dừng chức năng.[/yellow]")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]", default="")
    except Exception as exc:
        console.print(f"\n[bold red]Chức năng gặp lỗi:[/bold red] {exc}")
        Prompt.ask("\n[dim]Nhấn phím xác nhận để quay lại...[/dim]", default="")
    finally:
        # Xóa render cuối của các màn hình Live/Progress trước khi dựng menu.
        clear_screen()


def _draw_menu(title: str, rows: list[tuple[str, str]]) -> str:
    """Hiển thị menu và trả về lựa chọn."""
    show_header()
    table = Table(title=title, border_style="bold red", header_style="bold yellow", expand=False)
    table.add_column("STT", style="bold red", justify="center", width=5)
    table.add_column("Tính năng", style="bold white", min_width=34)
    for number, label in rows:
        table.add_row(number, label)
    console.print(table)
    return Prompt.ask("\n[bold red]Lựa chọn[/bold red]")


def _run_submenu(rows, actions, title) -> None:
    while True:
        choice = _draw_menu(title, rows)
        if choice == "0":
            return
        feature = actions.get(choice)
        if feature:
            _open_feature(feature)


def menu_vision() -> None:
    _run_submenu(
        [("1", "Mở camera"), ("2", "Tạo mã QR"), ("3", "Tạo mã vạch Code128"),
         ("4", "Quét mã QR bằng camera"), ("5", "Chụp màn hình"),
         ("6", "Xem hình ảnh trong cửa sổ lệnh"), ("0", "Quay lại menu chính")],
        {"1": feature_camera, "2": feature_qr, "3": feature_barcode, "4": feature_qr_scan,
         "5": feature_screenshot, "6": feature_terminal_image},
        "[1] THỊ GIÁC VÀ QUÉT MÃ",
    )


def menu_lookup() -> None:
    _run_submenu(
        [("1", "Tra cứu thời tiết"), ("2", "Tra cứu Pokémon và thẻ Pokémon"),
         ("3", "Bảng tuần hoàn hóa học"), ("4", "Tìm kiếm Wikipedia"), ("0", "Quay lại menu chính")],
        {"1": feature_weather, "2": feature_pokemon, "3": feature_element, "4": feature_wiki},
        "[2] TRA CỨU VÀ DỮ LIỆU",
    )


def menu_time() -> None:
    rows = [("1", "Đồng hồ hiện tại"), ("2", "Lịch tháng"), ("3", "Đếm ngược"),
            ("4", "Đồng hồ cà chua"), ("0", "Quay lại menu chính")]
    while True:
        choice = _draw_menu("[3] TRUNG TÂM THỜI GIAN", rows)
        if choice == "0":
            return
        if choice in {"1", "2", "3", "4"}:
            _open_feature(lambda c=choice: feature_time_center(c))


def menu_ai() -> None:
    _run_submenu(
        [("1", "Trò chuyện với trí tuệ nhân tạo"), ("2", "Chuyển văn bản thành giọng nói"),
         ("3", "Ghi âm"), ("4", "Tạo sách nói từ văn bản"), ("0", "Quay lại menu chính")],
        {"1": feature_ai_waifu, "2": feature_tts, "3": feature_voice_recorder, "4": feature_audiobook},
        "[4] TRÍ TUỆ NHÂN TẠO VÀ GIỌNG NÓI",
    )


def menu_media() -> None:
    _run_submenu(
        [("1", "Tải video hoặc nhạc từ YouTube"), ("2", "Trình phát nhạc Ragnarok"),
         ("3", "Gộp tệp PDF"), ("4", "Khóa tệp PDF bằng mật khẩu"),
         ("5", "Tách âm thanh từ video"), ("0", "Quay lại menu chính")],
        {"1": feature_downloader, "2": feature_media_player, "3": feature_pdf_merge,
         "4": feature_pdf_protect, "5": feature_audio_extract},
        "[5] ĐA PHƯƠNG TIỆN VÀ TỆP",
    )


def menu_system() -> None:
    _run_submenu(
        [("1", "Tạo mật khẩu ngẫu nhiên"), ("2", "Rút gọn hoặc giải mã địa chỉ web"),
         ("3", "Giám sát CPU, RAM, GPU, ổ đĩa và mạng"), ("0", "Quay lại menu chính")],
        {"1": feature_password, "2": feature_link_tool, "3": feature_system_monitor},
        "[6] CÔNG CỤ HỆ THỐNG",
    )


def main_menu() -> None:
    rows = [
        ("1", "Thị giác và quét mã"), ("2", "Tra cứu và dữ liệu"), ("3", "Trung tâm thời gian"),
        ("4", "Trí tuệ nhân tạo và giọng nói"), ("5", "Đa phương tiện và tệp"),
        ("6", "Công cụ hệ thống"), ("0", "Thoát chương trình"),
    ]
    actions = {"1": menu_vision, "2": menu_lookup, "3": menu_time, "4": menu_ai,
               "5": menu_media, "6": menu_system}
    while True:
        choice = _draw_menu("MENU CHÍNH", rows)
        if choice == "0":
            console.print("\n[bold green]Tạm biệt! Hẹn gặp lại.[/bold green]")
            return
        action = actions.get(choice)
        if action:
            action()
