"""
Shared Rich Console instance + áp dụng theme (màu chữ / kiểu chữ / màu nền).

QUAN TRỌNG: `console` ở đây chính là "global console" nội bộ của thư viện
Rich (rich.get_console()) chứ không phải một Console() mới. Rich.Prompt.ask()
và Confirm.ask() khi được gọi mà KHÔNG truyền tham số console= (đây là cách
gần như toàn bộ project đang dùng) sẽ tự động fallback về đúng instance này.

Nhờ vậy, khi người dùng đổi giao diện (tools/theme_settings.py), màu chữ /
kiểu chữ / màu nền áp dụng đồng bộ cho TOÀN BỘ chương trình -- kể cả các ô
nhập liệu Prompt/Confirm nằm rải rác trong hàng chục file tool -- mà không
cần sửa từng lời gọi.
"""

import rich

from theme import Theme, load_theme

console = rich.get_console()

_current_theme: "Theme | None" = None


def apply_theme(theme: "Theme | None" = None) -> None:
    """Áp một theme lên console dùng chung (đọc từ config nếu không truyền vào)."""
    global _current_theme
    _current_theme = theme or load_theme()
    console.style = _current_theme.console_base_style()


def get_current_theme() -> "Theme":
    """Trả về theme đang được áp dụng (tự load từ config nếu chưa apply lần nào)."""
    global _current_theme
    if _current_theme is None:
        apply_theme()
    return _current_theme


# Áp theme đã lưu (hoặc mặc định) ngay khi module được import lần đầu tiên,
# để mọi màn hình vẽ ra ngay từ đầu (banner, menu chính...) đã đúng giao diện.
apply_theme()
